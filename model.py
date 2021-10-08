import os
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression, Lasso, SGDRegressor
from sklearn import svm
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, Normalizer, MinMaxScaler
from joblib import dump, load
from abc import ABC, abstractmethod

class BaseModel(ABC):

    def __init__(self):
        self._model = None

    @property
    def model(self):
        return self._model

    @abstractmethod
    def train(self):
        pass

    @abstractmethod
    def load_model(self):
        pass

    @abstractmethod
    def predict(self):
        pass

class OwModel(BaseModel):

    def __init__(self):
        super().__init__()
        self._model_path = os.path.join('data', 'ow_sr_model.joblib')
    
    def train(
            self,
            generate_insight: bool = True,
            store_model: bool = True,
    ):
        df = pd.read_csv(os.path.join('data', 'ow_ratings.csv'), index_col=False).drop('query', axis=1)
        print(df.describe())
        print('count zeros:', df['skill_rating'].value_counts()[0])
        df = df[df['skill_rating']>0] # hard-pruning outliers
        df['ttl_games'] = df['wins']+df['losses']
        df = df[df['ttl_games']>=15] # placement matches can be up to 15
        df['win_perc'] = df['wins']/df['ttl_games']
        if generate_insight:
            df.plot(
                'ttl_games', 'skill_rating', kind='scatter'
            ).figure.savefig(os.path.join('data', 'ttl_games-skill_rating.pdf'))
            df.plot(
                'win_perc', 'skill_rating', kind='scatter'
            ).figure.savefig(os.path.join('data', 'win_perc-skill_rating.pdf'))
            df.plot(
                'wins', 'losses', kind='scatter'
            ).figure.savefig(os.path.join('data', 'wins_losses.pdf'))
            print(df.describe())
        x_train, x_test, y_train, y_test = train_test_split(
            df[['wins', 'losses']], df.skill_rating, test_size=0.2, random_state = 0
        )
        models = [
            LinearRegression(),
            svm.SVR(C=0.9, kernel='poly', degree=3),
            Lasso(alpha=0.8),
            SGDRegressor(max_iter=500),
        ]
        pipes = []
        for i, m in enumerate(models):
            pipe = Pipeline([('sc', Normalizer()), ('clf', m)]).fit(x_train.values, y_train.values)
            # print('LMS:', np.mean((pipe.predict(x_test) - y_test)**2))
            score = pipe.score(x_test.values, y_test.values)
            pipes.append((i, pipe, score))
            print(f'Score on test set ({type(pipe["clf"]).__name__}):', round(score, 4))
        self._model = max(pipes, key=lambda x: x[2])[1]
        if store_model:
            dump(pipe, self._model_path)
        return self
            
    def load_model(self):
        try:
            self._model = load(self._model_path)
        except:
            print('Model could not be loaded.')
        return self
    
    def predict(self, *args) -> int:
        if self._model is None:
            raise Exception('No model being used.')
        try:
            return int(
                self._model.predict(
                    np.array(args).reshape(1, -1)
                )[0]
            )
        except:
            print('Wrong input parameters.')
            return -1
    
if __name__ == '__main__':
    model = OwModel().train()
    model2 = OwModel().load_model()
    print(model2.predict(20, 100))