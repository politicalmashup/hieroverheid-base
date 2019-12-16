"""
This file was copied from https://github.com/elastic/elasticsearch-py/blob/e0fb772bcc011f21594535d0239cfc7a2c7acb95/elasticsearch/helpers/__init__.py
It is not meant to stay in use but was needed to solve an incompatibility issue with the ORI ES.
"""
import logging
import sys

from elasticsearch.helpers import ScanError

logger = logging.getLogger("elasticsearch.helpers")


def scan(
    client,
    query=None,
    scroll="5m",
    raise_on_error=True,
    preserve_order=False,
    size=1000,
    request_timeout=None,
    clear_scroll=True,
    scroll_kwargs=None,
    **kwargs
):
    """
    Simple abstraction on top of the
    :meth:`~elasticsearch.Elasticsearch.scroll` api - a simple iterator that
    yields all hits as returned by underlining scroll requests.

    By default scan does not return results in any pre-determined order. To
    have a standard order in the returned documents (either by score or
    explicit sort definition) when scrolling, use ``preserve_order=True``. This
    may be an expensive operation and will negate the performance benefits of
    using ``scan``.

    :arg client: instance of :class:`~elasticsearch.Elasticsearch` to use
    :arg query: body for the :meth:`~elasticsearch.Elasticsearch.search` api
    :arg scroll: Specify how long a consistent view of the index should be
        maintained for scrolled search
    :arg raise_on_error: raises an exception (``ScanError``) if an error is
        encountered (some shards fail to execute). By default we raise.
    :arg preserve_order: don't set the ``search_type`` to ``scan`` - this will
        cause the scroll to paginate with preserving the order. Note that this
        can be an extremely expensive operation and can easily lead to
        unpredictable results, use with caution.
    :arg size: size (per shard) of the batch send at each iteration.
    :arg request_timeout: explicit timeout for each call to ``scan``
    :arg clear_scroll: explicitly calls delete on the scroll id via the clear
        scroll API at the end of the method on completion or error, defaults
        to true.
    :arg scroll_kwargs: additional kwargs to be passed to
        :meth:`~elasticsearch.Elasticsearch.scroll`

    Any additional keyword arguments will be passed to the initial
    :meth:`~elasticsearch.Elasticsearch.search` call::

        scan(es,
            query={"query": {"match": {"title": "python"}}},
            index="orders-*",
            doc_type="books"
        )

    """
    scroll_kwargs = scroll_kwargs or {}

    if not preserve_order:
        query = query.copy() if query else {}
        query["sort"] = "_doc"
    # initial search
    resp = client.search(
        body=query, scroll=scroll, size=size, request_timeout=request_timeout, **kwargs
    )

    scroll_id = resp.get("_scroll_id")
    if scroll_id is None:
        return

    try:
        first_run = True
        while True:
            # if we didn't set search_type to scan initial search contains data
            if first_run:
                first_run = False
            else:
                resp = client.scroll(
                    scroll_id,
                    scroll=scroll,
                    request_timeout=request_timeout,
                    **scroll_kwargs
                )

            for hit in resp["hits"]["hits"]:
                yield hit

            # check if we have any errrors
            if resp["_shards"]["successful"] < resp["_shards"]["total"]:
                logger.warning(
                    "Scroll request has only succeeded on %d shards out of %d.",
                    resp["_shards"]["successful"],
                    resp["_shards"]["total"],
                )
                if raise_on_error:
                    raise ScanError(
                        scroll_id,
                        "Scroll request has only succeeded on %d shards out of %d."
                        % (resp["_shards"]["successful"], resp["_shards"]["total"]),
                    )

            scroll_id = resp.get("_scroll_id")
            # end of scroll
            if scroll_id is None or not resp["hits"]["hits"]:
                break
    finally:
        if scroll_id and clear_scroll:
            resp_data = client.transport.perform_request(
                "DELETE", f"/_search/scroll/{scroll_id}", params={'ignore': (404,)}
            )
            if not resp_data.get('succeeded'):
                print(
                    f'there was an issue clearing scroll context for {scroll_id}:\n',
                    resp_data,
                    file=sys.stderr
                )
