# The MIT License (MIT)
#
# Copyright (c) 2015 QuiteQuiet<https://github.com/QuiteQuiet>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from data.pokedex import Pokedex
from data.moves import Moves
from data.abilities import Abilities
from plugins.games import GenericGame
import re
import random
import datetime
import yaml

Scoreboard = {}
with open('plugins/scoreboard.yaml', 'a+') as yf:
    yf.seek(0, 0)
    Scoreboard = yaml.load(yf)
    if not Scoreboard: # Empty yaml file set Scoreboard to None, but a dict is expected
        Scoreboard = {}

class Anagram(GenericGame):
    def __init__(self):
        self.hints = []
        self.word, self.solution = self.newWord()
        self.startTime = datetime.datetime.now()

    def newWord(self):
        pokemon = list(Pokedex)
        moves = list(Moves)
        abilities = list(Abilities)
        pick = random.choice(pokemon+moves+abilities)
        if pick in Pokedex:
            self.hints.append("It's a pokemon!")
        elif pick in Moves:
            self.hints.append("It's a move!")
        elif pick in Abilities:
            self.hints.append("It's an ability!")
        self.hints.append("It begins with **{letter}**".format(letter = pick[0].upper()))
        pick = re.sub(r'[^a-zA-Z0-9]', '', pick.lower())
        anagram = list(pick)
        random.shuffle(anagram)
        return ''.join(anagram), pick

    def getHint(self):
        if not self.hints: return 'No more hints avaliable'
        hint = random.choice(self.hints)
        self.hints.remove(hint)
        return hint

    def getWord(self):
        return self.word

    def getSolvedWord(self):
        return self.solution

    def isCorrect(self, guess):
        return guess == self.solution

    def getSolveTimeStr(self):
        totalTime = datetime.datetime.now() - self.startTime
        if totalTime.seconds < 60:
            return ' in {time} seconds!'.format(time = totalTime.seconds)
        elif totalTime.seconds < 60 * 60: # Under 1 hour
            minutes = totalTime.seconds // 60
            return ' in {mins} minutes and {sec} seconds!'.format(mins = minutes, sec = totalTime.seconds-(minutes * 60))
        else:
            return '!'

def start(bot, cmd, room, msg, user):
    if msg == 'new':
        if not user.hasRank('%'):
            return 'You do not have permission to start a game in this room. (Requires %)', False
        if room.game:
            return 'A game is already running somewhere', False
        room.game = Anagram()
        return 'A new anagram has been created (guess with ~a):\n' + room.game.getWord(), True

    elif msg == 'hint':
        if room.game:
            return 'The hint is: ' + room.game.getHint(), True


    elif msg == 'end':
        if not user.hasRank('%'):
            return 'You do not have permission to end the anagram. (Requires %)', True
        if not (room.game and room.game.isThisGame(Anagram)): 
            return 'There is no active anagram or a different game is active.', False
        solved = room.game.getSolvedWord()
        room.game = None
        return 'The anagram was forcefully ended by {baduser}. (Killjoy)\nThe solution was: **{solved}**'.format(baduser = user.name, solved = solved), True

    elif msg.lower().startswith('score'):
        if msg.strip() == 'score': msg += ' {user}'.format(user = user.id)
        name = bot.toId(msg[len('score '):])
        if name not in Scoreboard: return "This user never won any anagrams", True
        return 'This user has won {number} anagram{plural}'.format(number = Scoreboard[name], plural = '' if not type(Scoreboard[name]) == str and Scoreboard[name] < 2  else 's'), True
    else:
        if msg: return '{param} is not a valid parameter for ~anagram. Make guesses with ~a'.format(param = msg), False
        if room.game and room.game.isThisGame(Anagram):
            return 'Current anagram: {word}'.format(word = room.game.getWord()), True
        return 'There is no active anagram right now', False

def answer(bot, cmd, room, msg, user):
    if not (room.game and room.game.isThisGame(Anagram)): return 'There is no anagram active right now', True
    if room.game.isCorrect(re.sub(r'[ -]', '', msg).lower()):
        solved = room.game.getSolvedWord()
        timeTaken = room.game.getSolveTimeStr()
        room.game = None
        # Save score
        Scoreboard[user.id] = 1 if user.id not in Scoreboard else Scoreboard[user.id] + 1
        with open('plugins/scoreboard.yaml', 'w') as ym:
            yaml.dump(Scoreboard, ym)
        return 'Congratulations, {name} got it{time}\nThe solution was: {solution}'.format(name = user.name, time = timeTaken, solution = solved), True
    return '{test} is wrong!'.format(test = msg.lstrip()), True
