from scrapy.exceptions import DropItem
from scrapy.http import Request
from scrapy.pipelines.files import FilesPipeline

import os
import hashlib
import logging
import urlparse
import urllib
import sqlite3

logger = logging.getLogger(__name__)

def init_database():
    conn = sqlite3.connect(database="firmware.db")
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS brand (id INTEGER PRIMARY KEY, name TEXT);")
    cur.execute("CREATE TABLE IF NOT EXISTS image (id INTEGER PRIMARY KEY, filename TEXT, description TEXT NULL, brand_id INTEGER, hash TEXT);")
    cur.execute("CREATE TABLE IF NOT EXISTS product (id INTEGER PRIMARY KEY, iid INTEGER, url TEXT, mib_filename TEXT, mib_url TEXT NULL, mib_hash TEXT, sdk_filename TEXT, sdk_url TEXT NULL, sdk_hash TEXT, product TEXT NULL, version TEXT NULL, build TEXT NULL, date TEXT);")
    return conn

class FirmwarePipeline(FilesPipeline):
    def __init__(self, store_uri, download_func=None, settings=None):
        self.database = init_database()
        super(FirmwarePipeline, self).__init__(store_uri, download_func,settings)

    @classmethod
    def from_settings(cls, settings):
        store_uri = settings['FILES_STORE']
        cls.expires = settings.getint('FILES_EXPIRES')
        cls.files_urls_field = settings.get('FILES_URLS_FIELD')
        cls.files_result_field = settings.get('FILES_RESULT_FIELD')

        return cls(store_uri, settings=settings)

    # overrides function from FilesPipeline
    def file_path(self, request, response=None, info=None):
        extension = os.path.splitext(os.path.basename(
            urlparse.urlsplit(request.url).path))[1]
        return "%s/%s%s" % (request.meta["vendor"],
                            hashlib.sha1(request.url).hexdigest(), extension)

    # overrides function from FilesPipeline
    def get_media_requests(self, item, info):
        # check for mandatory fields
        for x in ["vendor", "url"]:
            if x not in item:
                raise DropItem(
                    "Missing required field '%s' for item: " % (x, item))

        # resolve dynamic redirects in urls
        for x in ["mib", "sdk", "url"]:
            if x in item:
                split = urlparse.urlsplit(item[x])
                # remove username/password if only one provided
                if split.username or split.password and not (split.username and split.password):
                    item[x] = urlparse.urlunsplit(
                        (split[0], split[1][split[1].find("@") + 1:], split[2], split[3], split[4]))

                if split.scheme == "http":
                    item[x] = urllib.urlopen(item[x]).geturl()

        # check for filtered url types in path
        url = urlparse.urlparse(item["url"])
        if any(url.path.endswith(x) for x in [".pdf", ".php", ".txt", ".doc", ".rtf", ".docx", ".htm", ".html", ".md5", ".sha1", ".torrent"]):
            raise DropItem("Filtered path extension: %s" % url.path)
        elif any(x in url.path for x in ["driver", "utility", "install", "wizard", "gpl", "login"]):
            raise DropItem("Filtered path type: %s" % url.path)

        # generate list of url's to download
        item[self.files_urls_field] = [item[x]
                                       for x in ["mib", "url"] if x in item]

        # pass vendor so we can generate the correct file path and name
        return [Request(x, meta={"ftp_user": "anonymous", "ftp_password": "chrome@example.com", "vendor": item["vendor"]}) for x in item[self.files_urls_field]]

    # overrides function from FilesPipeline
    def item_completed(self, results, item, info):
        item[self.files_result_field] = []
        if isinstance(item, dict) or self.files_result_field in item.fields:
            item[self.files_result_field] = [x for ok, x in results if ok]


        if self.database:
            try:
                cur = self.database.cursor()
                # create mapping between input URL fields and results for each
                # URL
                status = {}
                for ok, x in results:
                    for y in ["mib", "url", "sdk"]:
                        # verify URL's are the same after unquoting
                        if ok and y in item and urllib.unquote(item[y]) == urllib.unquote(x["url"]):
                            status[y] = x
                        elif y not in status:
                            status[y] = {"checksum": None, "path": None}

                if not status["url"]["path"]:
                    logger.warning("Empty filename for image: %s!" % item)
                    return item

                # attempt to find a matching image_id
                cur.execute("SELECT id FROM image WHERE hash=(?)",
                            (status["url"]["checksum"],))
                image_id = cur.fetchone()

                if not image_id:
                    cur.execute("SELECT id FROM brand WHERE name=(?)", (item["vendor"],))
                    brand_id = cur.fetchone()

                    if not brand_id:
                        cur.execute("INSERT INTO brand (name) VALUES (?)", (item["vendor"],))
                        cur.execute("SELECT last_insert_rowid()")
                        brand_id = cur.fetchone()[0]
                        logger.info("Inserted database entry for brand: %d!" % brand_id)
                    else:
                        brand_id = brand_id[0]
                    cur.execute("INSERT INTO image (filename, description, brand_id, hash) VALUES (?, ?, ?, ?)",
                                (status["url"]["path"], item.get("description", None), brand_id, status["url"]["checksum"]))
                    cur.execute("SELECT last_insert_rowid()")
                    image_id = cur.fetchone()[0]
                    logger.info("Inserted database entry for image: %d!" % image_id)
                else:
                    image_id = image_id[0]
                    cur.execute("SELECT filename FROM image WHERE hash=(?)",
                                (status["url"]["checksum"], ))
                    path = cur.fetchone()

                    logger.info(
                        "Found existing database entry for image: %d!" % image_id)
                    if path[0] != status["url"]["path"]:
                        os.remove(os.path.join(self.store.basedir,
                                               status["url"]["path"]))
                        logger.info("Removing duplicate file: %s!" %
                                    status["url"]["path"])

                # attempt to find a matching product_id
                def mk_sql(a, b):
                    return "EXISTS(SELECT %s INTERSECT SELECT '%s')" % (a, b)

                keys = ['product', 'version', 'build']
                values = map(lambda x: item.get(x, None), keys)
                sql = "SELECT id FROM product WHERE iid=(?) AND " + " AND ".join(map(mk_sql, keys, values))

                cur.execute(sql, (image_id,))
                product_id = cur.fetchone()

                if not product_id:
                    cur.execute("INSERT INTO product (iid, url, mib_filename, mib_url, mib_hash, sdk_filename, sdk_url, sdk_hash, product, version, build, date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                (image_id, item["url"], status["mib"]["path"], item.get("mib", None), status["mib"]["checksum"], status["sdk"]["path"], item.get("sdk", None), status["sdk"]["checksum"], item.get("product", None), item.get("version", None), item.get("build", None), item.get("date", None)))
                    cur.execute("SELECT last_insert_rowid()")
                    product_id = cur.fetchone()[0]
                    logger.info(
                        "Inserted database entry for product: %d!" % product_id)
                else:

                    cur.execute("UPDATE product SET iid=(?), url=(?), mib_filename=(?), mib_url=(?), mib_hash=(?), sdk_filename=(?), sdk_url=(?), sdk_hash=(?), product=(?), version=(?), build=(?), date=(?) WHERE id=(?)",
                                (image_id, item["url"], status["mib"]["path"], item.get("mib", None), status["mib"]["checksum"], status["sdk"]["path"], item.get("sdk", None), status["sdk"]["checksum"], item.get("product", None), item.get("version", None), item.get("build", None), item.get("date", None), image_id))
                    logger.info("Updated database entry for product: %d!" % product_id[0])

                self.database.commit()

            except BaseException as e:
                self.database.rollback()
                logger.warning("Database connection exception: %s!" % e)
                raise
            finally:
                if self.database and cur:
                    cur.close()

        return item
