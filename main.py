import os, io
from google.cloud import vision
from google.cloud.vision_v1 import types
import pandas as pd
import chess
import chess.pgn
import re

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'chess-notation-classifier-e30c1b944e9b.json'

client = vision.ImageAnnotatorClient()

def detectText(img):
    with open(img, 'rb') as image_file:
        content = image_file.read()

    image = types.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations

    df = pd.DataFrame(columns=['locale','description'])

    for text in texts:
        df = df.append(
            dict(
                locale=text.locale,
                description=text.description
            ),
            ignore_index=True
        )
    return df

def detectHandWriting(img):
    with open(img, 'rb') as image_file:
        content = image_file.read()

    image = types.Image(content=content)

    response = client.document_text_detection(image=image)
    docText = response.full_text_annotation.text
    print(docText)
    words_confidences = []
    
    pages = response.full_text_annotation.pages
    for page in pages:
        for block in page.blocks:
            print('block confidence:', block.confidence)

            for paragraph in block.paragraphs:
                print('paragraph confidence:', paragraph.confidence)

                for word in paragraph.words:
                    word_text = ''.join([symbol.text for symbol in word.symbols])
                    words_confidences.append([word_text, word.confidence])
                    print('Word text: {0} (confidence: {1}'.format(word_text, word.confidence))
    return words_confidences

def generatePGN(event, site, date, roundNum, white, black, result, game):
    game = chess.pgn.Game()
    
    game.headers["Event"] = event
    game.headers["Site"] = site
    game.headers["Date"] = date
    game.headers["Round"] = roundNum
    game.headers["White"] = white
    game.headers["Black"] = black
    game.headers["Result"] = result


    return game
     
def cleanData(words, confidences):
    white = 0
    black = 0
    while True:
        if 'WHITE' not in words or 'BLACK' not in words:
            break
        
        white = words.index('WHITE', white+1)
        black = words.index('BLACK', black+1)

        if white + 1 == black:
            break
    
    words = words[black+1:]
    count = 0
    stop_index = len(words) - 1
    for word in words:
        numeric = False
        for char in word:
            if char.isdigit():
                numeric = True
                break
        if len(word) > 4 and word != "BLACK" and word != "WHITE" and not numeric:
            count += 1
        if count > 1:
            stop_index = words.index(word)
            break

    words = words[:stop_index]

    for x in range(len(words)):
        if confidences[x] < 0.1:
            words[x] = ''
        words[x] = words[x].replace('s', '5')
        words[x] = words[x].replace('b', '6')
        words[x] = words[x].replace('l', '1')
        words[x] = words[x].replace('i', '1')
        words[x] = words[x].replace('<', 'c')
        words[x] = words[x].replace('.', '')
        words[x] = words[x].replace('_', '')
        
            
    
    words = list(filter(None, words))
    return words

FILE_NAME = 'carbonless-scorepad_1.jpg'
FOLDER_PATH = '/Users/colinzhu/Downloads'
#detectText(os.path.join(FOLDER_PATH, FILE_NAME))
IMAGE_FILE = 'chess_test3.jpg'
temp = detectHandWriting(os.path.join(FOLDER_PATH, IMAGE_FILE))

words = [] #get words 
confidences = [] #get corresponding confidences 
for pair in temp:
    words.append(pair[0])
    confidences.append(pair[1])


moves = cleanData(words, confidences)
move_set = {}
moves_clean = []
print(moves)

for move in moves:
    if move == 'BLACK' or move == 'WHITE':
        continue
    else:
        m = re.search(r'\d+$', move)
        # if the string ends in digits m will be a Match object, or None otherwise.
        if m is None:
            index = moves.index(move)
            if moves[index+1].isnumeric():
                moves_clean.append(move+moves[index+1])
                moves.remove(moves[index+1])
        else:
            moves_clean.append(move)

if moves_clean[0] != 1:
    moves_clean.insert(0, '1')

#print(moves_clean)
