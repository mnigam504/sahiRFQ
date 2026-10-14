"""Supervised category routing and three inspectable retrieval signals."""
import hashlib
import json
from pathlib import Path

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import Normalizer

ROOT = Path(__file__).resolve().parents[1]


def load_json(name):
    return json.loads((ROOT / 'data' / name).read_text(encoding='utf-8'))


class Router:
    """TF-IDF word/character features -> logistic regression.

    Scores are model probabilities on this toy distribution, NOT calibrated
    real-world confidence. Routing also uses explicit coverage/ambiguity gates.
    """
    def __init__(self, rows=None):
        rows = load_json('training.json') if rows is None else rows
        self.model = Pipeline([
            ('features', FeatureUnion([
                ('word', TfidfVectorizer(ngram_range=(1,2), sublinear_tf=True)),
                ('char', TfidfVectorizer(analyzer='char_wb', ngram_range=(3,5), sublinear_tf=True)),
            ])),
            ('classifier', LogisticRegression(C=8, max_iter=1000, random_state=42))
        ])
        self.model.fit([r['text'] for r in rows], [r['category'] for r in rows])
        self.training_count = len(rows)

    def predict(self, text):
        probs = self.model.predict_proba([text])[0]
        order = np.argsort(probs)[::-1]
        return [{'category':str(self.model.classes_[i]), 'probability':round(float(probs[i]),4)} for i in order]


class CatalogIndex:
    """Word + typo-tolerant character TF-IDF + learned dense LSA vectors.

    This is not a transformer embedding model. LSA is a learned linear
    projection of catalog TF-IDF vectors, fitted only on the catalog.
    """
    def __init__(self, records):
        self.records = records
        texts = [self.document(r) for r in records]
        self.word = TfidfVectorizer(ngram_range=(1,2), sublinear_tf=True)
        self.char = TfidfVectorizer(analyzer='char_wb', ngram_range=(3,5), sublinear_tf=True)
        self.wmat = self.word.fit_transform(texts)
        self.cmat = self.char.fit_transform(texts)
        self.svd = TruncatedSVD(n_components=min(16,len(records)-1), random_state=42)
        self.normalizer = Normalizer()
        self.dmat = self.normalizer.fit_transform(self.svd.fit_transform(self.wmat))
        self.fingerprint = hashlib.sha256(json.dumps(records,sort_keys=True).encode()).hexdigest()[:12]

    @staticmethod
    def document(r):
        # Values are searchable, but only structured fields establish eligibility.
        specs = ' '.join(f'{k} {v}' for k,v in r['specs'].items() if v is not None)
        return f"{r['title']} {r['category'].replace('_',' ')} {r['dispatch_city']} {specs}"

    def search(self, text):
        wq = self.word.transform([text])
        cq = self.char.transform([text])
        dq = self.normalizer.transform(self.svd.transform(wq))
        word = (self.wmat @ wq.T).toarray().ravel()
        char = (self.cmat @ cq.T).toarray().ravel()
        dense = self.dmat @ dq.ravel()
        scores = .55*word + .30*char + .15*np.clip(dense,0,1)
        return [{'record':r, 'score':round(float(scores[i]),5),
                 'signals':{'word':round(float(word[i]),4),'char':round(float(char[i]),4),'lsa':round(float(dense[i]),4)}}
                for i,r in sorted(enumerate(self.records),key=lambda x:(-scores[x[0]],x[1]['id']))]
