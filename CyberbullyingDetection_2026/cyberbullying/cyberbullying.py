import string
import pickle
import re

import nltk
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
from nltk.tokenize import word_tokenize

from cyberbullying import constants

nltk.download("stopwords")

ps = PorterStemmer()

from cyberbullying.constants import datasetpath
from cyberbullying.sentimentanalyzer import getCommentSentiment

def emojiremoval(item):

    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               u"\U00002702-\U000027B0"  # other emoticons
                               u"\U0001F923"  # rolf emoji
                               u"\U000024C2-\U0001F251" "]+", flags=re.UNICODE)
    return "".join(emoji_pattern.sub(r'', item)) + "\n"

def normalizing(item):

    # tokenize the sentences
    tokens = word_tokenize(item)

    # convert to lower case
    tokens = [w.lower() for w in tokens]

    # remove punctuation from each word
    table = str.maketrans('', '', string.punctuation)
    tokens = [w.translate(table) for w in tokens]

    # remove stopwords from each sentence
    stop_words = set(stopwords.words('english'))
    tokens = [w for w in tokens if not w in stop_words]

    return " ".join(tokens) + "\n"

def isBullyingPost(comment):

    comment = str(emojiremoval(comment))
    comment = str(normalizing(comment))
    sentiment = getCommentSentiment(comment)

    tokens = word_tokenize(comment)

    tokenlist = []

    for i in tokens:
        if len(i) >= 3 and i.isalpha():
            tokenlist.append(i)

    i = 0

    badwords = []

    filenames = [
        datasetpath+'Hurtful.txt',
        datasetpath+'Obscene.txt',
        datasetpath+'Insults.txt',
        datasetpath+'Racist.txt']

    while i != 4:
        with open(filenames[i]) as infile:
            for line in infile:
                line = line[:-1]
                line.strip()
                badwords.append(line)
            i += 1
    flag = 0

    for t in tokenlist:
        for i in badwords:
            if i == t:
                flag = 1
    if flag == 1:
        return True
    else:
        return False


def load_pkl(fname):
    with open(fname, 'rb') as f:
        obj = pickle.load(f)
    return obj

model =load_pkl(constants.modelpath+"xgb.pkl")

def preprocess_post(post):
    p_post = re.sub('[^a-zA-Z]', ' ',post)
    p_post = p_post.lower().split()
    p_post = [ps.stem(word) for word in p_post if word not in stopwords.words('english')]
    p_post = ' '.join(p_post)
    return p_post

def isCyberbullyingPost(post):

    isbullying_flag=False;

    post = preprocess_post(post)

    prediction = model.predict([post])

    if prediction[0] in [0, 1, 2, 5]:
        isbullying_flag = True

    return isbullying_flag