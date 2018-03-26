from janome.tokenizer import Tokenizer
import pandas as pd
import csv
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import AgglomerativeClustering


FILE_NAME = 'restaurant.csv'

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)


def tokenize(text):
    if pd.isnull(text):
        return ['']
    t = Tokenizer()
    parts = ('名詞', '動詞', '形容詞', '助動詞')
    token_list = []
    for token in t.tokenize(text):
        if token.part_of_speech.split(',')[0] in parts:
            token_list.append(token.surface)
    return token_list


def build_tokens(df):
    texts = [[' '.join(tokens)] for tokens in map(tokenize, df['comment'])]
    tokens_df = pd.DataFrame(texts)
    return tokens_df


def build_tfidf(tokens_df):
    tokens_df = tokens_df.fillna('')
    texts = tokens_df.iloc[:, 0]
    vectorizer_t = TfidfVectorizer()
    vectorizer_t.fit(texts)
    result = vectorizer_t.transform(texts).toarray()
    columns = vectorizer_t.get_feature_names()
    X = pd.DataFrame(result, columns=columns)
    return X


def get_clusters(X):
    model = model = AgglomerativeClustering(n_clusters=10)
    y_pred = model.fit_predict(X)
    # df = pd.DataFrame()
    # df['cluster'] = y_pred
    # df['score'] = silhouette_samples(X, y_pred)
    # d = df.groupby('cluster').mean()
    # d = dict(zip(d.index, d.values[:, 0]))
    # df['score_mean'] = df['cluster'].map(d)
    # return df['cluster'].values, \
    #        df['score'].values, \
    #        df['score_mean'].values


if __name__ == '__main__':
    df = pd.read_csv(FILE_NAME, encoding='utf8', quoting=csv.QUOTE_ALL)
    df['comment'] = df['コメント'].str.cat(df['キーワード'], sep='')
    logging.info('Started tokenizing')
    tokens_df = build_tokens(df)
    logging.info('Started building tfidf')
    X = build_tfidf(tokens_df)
