""" Depreciated utilities functions and methods that uses threading instead of async.
Async with aoihttp speedups is more reliable than threading and shares a single session
Threading requires uwsgi config - which has a performance impact:
uwsgi.config
enable-threads = True
threads = 20
processes = 4
"""
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor
import json
from django.http import QueryDict
import requests
import threading

thread_local = threading.local()


def thread_retrieve_external(util_arg_list: list) -> list:
    """Threading master function for loading external service data

    :param util_arg_list: List with service util argument tuples
    :type util_arg_list: ServiceUtils

    :return: list of threading tuple results
    :rtype: list
    """
    new_result_list = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        for result in executor.map(retrieve_external_service, util_arg_list):
            new_result_list.append(result)
    return new_result_list


def retrieve_external_service(util_arg: namedtuple) -> namedtuple:
    """Fetch data and loads into ServiceUtils instance
    using threadlocal request session if found.

    :param namedtuple: (group_key, ServiceUtil)
    :type util_arg: namedtuple(str, ServiceUtil)

    :return: (group_key and ServiceUtil)
    :rtype: namedtuple or None
    """
    util_arg.service_util.retrieve_value()
    return util_arg


def get_session() -> thread_local:
    """Get thread local request session"""
    if not hasattr(thread_local, "session"):
        thread_local.session = requests.Session()
    return thread_local.session


class ServiceUtils():
    """Threadsafe service methods to replace async methods if threading is required.
    Init method calls ORM so should be done before thread logic.
    """
    def request_data(self, parameters: dict, query: str = "?") -> dict:
        """Generates final query URL and fetches data.

        :param parameters: parameters to urlencode
        :type parameters: dict

        :param query: Url query delimiter
        :type query: str (default '?')

        :return: json response
        :rtype: dict
        """
        query_dict = QueryDict('', mutable=True)
        query_dict.update(parameters)
        if '?' in self.url:
            query_url = f'{self.url}&{query_dict.urlencode()}'
        else:
            query_url = f'{self.url}{query}{query_dict.urlencode()}'

        session = get_session()
        with session.get(query_url) as response:
            if response.status_code == 200:
                self.source_uri = query_url
                return json.loads(response.content)
