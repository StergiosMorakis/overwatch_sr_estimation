import os
import pandas as pd
import numpy as np
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

class DataCollector:
    def __init__(self):
        self._adjust_path = lambda filename=None: os.path.join(     # return str "data/ow_ratings.csv"
            'data', filename                                        # if default parameter
        ) if isinstance(filename, str) else os.path.join(           # else f"data/{filename}"
            'data', f'ow_ratings.csv'
        )
        self._dataset = self._load_data()                           # pd.DataFrame if "ow_ratings.csv" file exists else None

    def _gen_search_queries(self):
        ''' Search query generator '''
        query_generator = self._gen_lookup_queries()
        if isinstance(
            self._dataset, pd.DataFrame
        ):
            latest_query = self._dataset['query'].iloc[-1]
            # get iterator just after the latest searched term in cache
            while next(query_generator) != latest_query:
                continue
        for query in query_generator:
            yield query

    def _gen_lookup_queries(self):

        def _gen_ow_competetive_usernames(
            filename: str = 'overwatch-diary.csv'
        ):
            ''' Competetive player generator '''
            df = pd.read_csv(self._adjust_path(filename))
            for competetive_username in (
                username for username in np.unique(
                    df.loc[:, [
                        f'my_team_{i}' for i in range(1, 7)
                    ]].fillna('').values
                ) 
                if len(username)>1
            ):
                yield competetive_username.lower()
                
        def _gen_ow_hero_names():
            ''' Hero name generator '''
            for hero_name in (
                'Tracer', 'Reaper', 'Widowmaker', 'Pharah', 'Reinhardt', 'Mercy',
                'Torbjorn', 'Hanzo', 'Winston', 'Zenyatta', 'Bastion', 'Symmetra',
                'Zarya', 'McCree', 'Soldier76', 'Lucio', 'Roadhog', 'Junkrat', 'DVa',
                'Mei', 'Genji', 'Ana', 'Sombra', 'Orisa', 'Doomfist', 'Moira', 'Brigitte',
                'WreckingBall', 'Ashe', 'Baptiste', 'Sigma', 'Echo', 'Sojourn', 'Brit',
                'Bruiser', 'Firestarter', 'Frost', 'Helio', 'Hivemind', 'Huntress',
                'JetpackCat',  'Luc', 'MamaHong',  'McCloud', 'Overmind', 'Phreak',
                'Praetor', 'Psyblade', 'Rashi', 'Recluse', 'Rumble', 'ShieldGuy', 
                'Troy', 'Watcher', 'Yetzi',
            ):
                yield hero_name.lower()

        yield from _gen_ow_competetive_usernames()
        yield from _gen_ow_hero_names()

    def _load_data(self):
        data_filepath = self._adjust_path()
        if os.path.exists(data_filepath):
            return pd.read_csv(data_filepath, index_col=False)

    def _open_browser(self):
        options = Options()
        options.headless = True
        firefox_profile = webdriver.FirefoxProfile()
        firefox_profile.set_preference(
            "browser.privatebrowsing.autostart",
            True
        )
        browser = webdriver.Firefox(
            options=options,
            executable_path='./drivers/geckodriver',
            firefox_profile=firefox_profile
        )
        return browser

    def generate_dataset(self):
        ''' webscrap accounts found using self.queries values '''
        retrieved_data, errors, batch_size = [], 0, 500
        browser, max_delay = self._open_browser(), 30 # secs
        for query in self._gen_search_queries():
            try:
                try:
                    browser.get('https://overwatch.op.gg/search/?playerName={}'.format(query))
                except:
                    raise Exception(f'Server failure - "https://overwatch.op.gg/search/?playerName={query}".')
                try:
                    results_len = int(
                        WebDriverWait(browser, max_delay).until(
                            EC.visibility_of_element_located(
                                (By.CSS_SELECTOR, 'h2.Title > small:nth-child(2)')
                            )
                        ).text[1:-1]
                    )
                except:
                    raise Exception(f'No data could be retrieved for username "{query}".')
                page_loader_counter = (results_len-1)//25 # paging length
                for i in range(page_loader_counter):
                    # scroll to the bottom of the page (for displaying more results)
                    browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    WebDriverWait(browser, max_delay).until(
                        EC.element_to_be_clickable(
                            (
                                By.CSS_SELECTOR,
                                f".LeaderBoardsTable > tbody:nth-child(2) > tr:nth-child({(i+1)*25+1})"
                            )
                        )
                    )
                for i in range(1, results_len+1):
                    console = browser.find_element_by_css_selector(
                        f'.LeaderBoardsTable > tbody:nth-child(2) > tr:nth-child({i}) > td:nth-child(2)'
                    ).text
                    if console == 'PC':
                        # collect only PC accounts
                        try:
                            skill_rating = int(
                                browser.find_element_by_css_selector(
                                    f'.LeaderBoardsTable > tbody:nth-child(2) > tr:nth-child({i}) > td:nth-child(4)'
                                ).text
                            )
                            ttl_wins = int(
                                browser.find_element_by_css_selector(
                                    (
                                        'body > div.l-wrap.l-wrap-- > div > div.SearchPlayerLayout > div.Content > table > tbody > '
                                        f'tr:nth-child({i})'
                                        ' > td.ContentCell.ContentCell-WinRatio > div > div.WinLose > div.Win'
                                    )
                                ).text[:-1]
                            )
                            ttl_losses = int(
                                browser.find_element_by_css_selector(
                                    (
                                        'body > div.l-wrap.l-wrap-- > div > div.SearchPlayerLayout > div.Content > table > tbody > '
                                        f'tr:nth-child({i})'
                                        ' > td.ContentCell.ContentCell-WinRatio > div > div.WinLose > div.Lose'
                                    )
                                ).text[:-1]
                            )
                            retrieved_data.append(
                                (query, ttl_wins, ttl_losses, skill_rating)
                            )
                            if len(retrieved_data) % batch_size == 0:
                                self._cache_retrieved_data(retrieved_data)
                                print('Batch cached.\nTtl results:', self._dataset.shape[0], 'Errors:', errors)
                                retrieved_data, errors = [], 0
                        except:
                            raise Exception(f'Failed entry retrieval for username "{query}".')
            except Exception as e:
                errors += 1
                print('Error occured -', e)
        browser.quit()
        self._cache_retrieved_data(retrieved_data)
        print('Job finished.\nTtl results:', self._dataset.shape[0], 'Errors:', errors)
        return self

    def _cache_retrieved_data(self, data):
        try:
            new_df = pd.DataFrame(data, columns = ['query', 'wins', 'losses', 'skill_rating'])
            if isinstance(self._dataset, pd.DataFrame):
                self._dataset = pd.concat([
                    self._dataset,
                    new_df
                ], join="inner")
            else:
                self._dataset = new_df
            self._dataset.to_csv(self._adjust_path(), index=False)
        except Exception as e: 
            print('Exception while storing data:', e)
        
if __name__ == '__main__':
    dc = DataCollector().generate_dataset()
