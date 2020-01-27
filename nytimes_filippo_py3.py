from __future__ import print_function
import argparse
import logging
import requests
from pprint import pprint
import time
import json

logging.basicConfig(filename='app.log', filemode='w', level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

class NYTimesSource(): #(object):
    """
    A data loader plugin for the NY Times API.
    """

    def __init__(self, config: dict):
        self._api_key = config['api_key']
        self._api = config['api']
        self._query = config['query']
        self._filter_query = config['fq']

    def connect(self, inc_column=None, max_inc_value=None):
        log.debug('Incremental Column: %r', inc_column)
        log.debug('Incremental Last Value: %r', max_inc_value)

    def disconnect(self):
        """Disconnect from the source."""
        # Nothing to do
        pass

    def flattenDict(self, d: dict, parent_key: str='', sep: str='.') -> dict:
        """
        Flatten a dictionary.

        NOTE: this method only flattens a dictionary.
        If the value is a list, it won't be flattened.
        This is simply an implementation choice.

        Attributes
        ----------
        d: dict
            Input dictionary to be flattened.
        parent_key: str
            Parent key.
        sep: str
            Separator to be used when merging keys.

        Returns
        -------
        d_flat: dict
            Flattened dictionary
        """
        d_flat = dict()
        for k, v in d.items():
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, dict):
                d_flat.update(self.flattenDict(v, new_key, sep=sep).items())
            else:
                d_flat[new_key] = v
        return d_flat

    def getDataBatch(self, batch_size: int=10, max_pages: int=100, page: int=None, wait_code429: bool=False) -> dict:
        """
        Generator - Get data from source on batches.

        Parameters
        ----------
        batch_size: int
            Size of the batch. Currently, the API fixes this to 10.
        max_pages: int
            Max number of pages to paginate through.
        page: int
            Specific page to get.
        wait_code429: bool
            If True, the generator waits until the limit expires.
            If False, it raises an error.

        Returns
        -------
        One list for each batch. Each of those is a list of
                 dictionaries with the defined rows.
        """
        if page:
            page_range = [page]
        else:
            page_range = range(max_pages)
        t_start = time.time()
        # Iterate over pages of 10 articles each
        for page in page_range:
            # Parameters for the query
            params = {
                'query': self._query,
                'api-key': self._api_key,
                'fq': self._filter_query,
                'page': page
            }

            # responses = requests.get(self._api, params).json()['response']['meta']
            responses = requests.get(self._api, params)

            # Check status code - from developer.nytimes.com
            if responses.status_code == 401:
                raise Warning('Code 401: Unauthorized request. Make sure api-key is set.')
            elif responses.status_code == 429:
                if wait_code429:
                    print('Code 429: Too many requests. You reached your per minute or per day rate limit.')
                    t_sleep = 60 - (time.time() - t_start) + 1
                    print(f"Let's wait {t_sleep:.0f}s before repeating the request")
                    time.sleep(t_sleep)
                    responses = requests.get(self._api, params)
                    # Reset
                    t_start = time.time()
                else:
                    raise Warning('Code 429: Too many requests. You reached your per minute or per day rate limit.')

            # Convert the responses to JSON and extract the articles
            responses = responses.json()['response']['docs']

            # Returns a list of flattened dictionaries
            yield [self.flattenDict(response) for response in responses]

    @staticmethod
    def getSchema() -> list:
        """
        Return the schema of the dataset
        Returns
        -------
        schema: list
            List containing the names of the columns retrieved from the source
        """

        schema = [
            'abstract',
            'web_url',
            'snippet',
            'lead_paragraph',
            'source',
            'multimedia',
            'headline.main',
            'headline.kicker',
            'headline.content_kicker',
            'headline.print_headline',
            'headline.name',
            'headline.seo',
            'headline.sub',
            'keywords',
            'pub_date',
            'document_type',
            'news_desk',
            'section_name',
            'byline.original',
            'byline.person',
            'byline.organization',
            'type_of_material',
            '_id',
            'word_count',
            'uri'
        ]

        return schema

if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Get articles from the NYT API")
    parser.add_argument('--query', required=True, type=str, help='Item to search')
    parser.add_argument('--api-key', required=True, type=str, help='API key')
    parser.add_argument('--max-pages', default=15, type=int, help='Max number of pages to paginate through')
    parser.add_argument('--fq', type=str, help="Filter the query: 'news_desk:('Washington')'")
    parser.add_argument('--wait-code429', action='store_true', default=False, help="It waits until the per minute limit expires.")
    args = parser.parse_args()

    # Define a few configuration parameters
    config = {
        'api_key': args.api_key,
        'api': 'https://api.nytimes.com/svc/search/v2/articlesearch.json',
        'query': args.query,
        'fq': args.fq
    }

    # Create source object
    source = NYTimesSource(config)

    # IMPORTANT
    # There is a limit of 10 queries per minute
    # If the --wait-code429 flag is used in the command line,
    # then getDataBatch will pause and wait till the limit expires.

    # Batch size
    # This number is fixed by the API:
    # "The Article Search API returns a max of 10 results at a time."
    # However, it is possible to use the page query parameter
    # to paginate through results (page=0 for results 1-10, page=1 for 11-20, ...).
    # It is possible to paginate through up to 100 pages (1,000 results).
    batch_size = 10

    # This looks like an argparse dependency - but the Namespace class is just
    # a simple way to create an object holding attributes.
    # source.args = argparse.Namespace(**config)

    # Get the articles
    for idx, batch in enumerate(source.getDataBatch(batch_size, max_pages=args.max_pages, wait_code429=args.wait_code429)):
        print(f"{idx} Batch of {len(batch)} items")
        for item in batch:
            print(f"\t- {item['_id']} - {item['headline.main']}")

    log.debug('End of query')