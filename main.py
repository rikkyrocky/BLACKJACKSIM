# Credit for basic strategy CSV goes to: https://github.com/RochesterinNYC/BlackjackStrategyTester
import random
import pandas as pd
import time
import numpy as np
BASIC_STRATEGY_TABLE = pd.read_csv('rsc/blackjackstrategychart.csv')
bankrolls = pd.Series(np.nan, index=range(1000))

class Deck:
    count = 0
    num_decks = 0
    suits = ['hearts', 'diamonds', 'clubs', 'spades']
    values = ['two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'jack', 'queen', 'king',
              'ace']

    def __init__(self, num_decks):
        self.num_decks = num_decks
        self.cards = [Card(suit, value) for _ in range(num_decks) for suit in self.suits for value in self.values]
        self.cards_remaining = 52 * num_decks

    def reshuffle(self):
        self.cards.clear()
        self.cards = [Card(suit, value) for _ in range(self.num_decks) for suit in self.suits for value in self.values]
        self.cards_remaining = 52 * self.num_decks

    def draw(self, face_up=True):
        # Use the current time to seed the random number generator
        current_time = time.time()
        random.seed(current_time)

        random_card = random.randint(0, self.get_cards_remaining() - 1)
        self.cards_remaining -= 1
        self.cards[random_card].face_up = face_up
        return self.cards.pop(random_card)

    def get_cards_remaining(self):
        return self.cards_remaining

    def get_cards_list(self):
        return self.cards


class Player:
    stake = 0
    bets = {}
    initial_bet = 0

    def __init__(self, bankroll, ABPTC):  # ABPTC = additional bet per true count
        self.bankroll = bankroll
        self.ABPTC = ABPTC

    # Hit: 1
    # Stand: 2
    # Split: 3
    # Double Down, hit otherwise: 4
    # Double Down, stand otherwise: 5

    def make_decision(self, table, player_num):
        decision_dict = {1: "Hit",
                         2: "Stand",
                         3: "Split",
                         4: "Double",
                         5: "Double",
                         }

        player_cards = table.get_player_cards(player_num)
        dealer_card = table.get_dealer_card()
        player_ace = False
        pair = False
        if len(player_cards) == 2:
            if player_cards[0].value == player_cards[1].value:
                pair = True
        if pair:
            for card in player_cards:
                number = card.numerical_value
                if number == 11:
                    number = 'A'
            row_index = f"{number} | {number}"
            return basic_strategy(row_index, dealer_card.numerical_value)
        player_card_sum = 0
        for card in table.get_player_cards(player_num):
            player_card_sum += card.numerical_value
        if player_card_sum > 21:
            for card in table.get_player_cards(player_num):
                if card.value == 'ace' and card.numerical_value == 11:
                    card.set_ace_1()
                    player_card_sum -= 10
                    if player_card_sum <= 21:
                        break
        for card in table.get_player_cards(player_num):
            if card.value == 'ace' and card.numerical_value == 11:
                player_ace = True
        if player_ace:
            row_index = f"A-{player_card_sum - 11}"
            print(decision_dict[basic_strategy(row_index, dealer_card.numerical_value)])
            return basic_strategy(row_index, dealer_card.numerical_value)
        else:
            print(decision_dict[basic_strategy(player_card_sum, dealer_card.numerical_value)])
            return basic_strategy(player_card_sum, dealer_card.numerical_value)

    def win(self, player_num, blackjack=False):
        print("BETS1: " + str(self.bets))
        print("win " + str(self.bets[f'player {player_num + 1}']))
        if blackjack:
            self.bankroll += self.bets[f'player {player_num + 1}'] * 1.5
        else:
            self.bankroll += self.bets[f'player {player_num + 1}']
        self.bets.pop(f'player {player_num + 1}')

    def lose(self, player_num):
        print("BETS2: " + str(self.bets))
        print("lose " + str(self.bets[f'player {player_num + 1}']))
        self.bankroll -= self.bets[f'player {player_num + 1}']
        self.bets.pop(f'player {player_num + 1}')

    def bet(self, true_count, min_bet, player_num=0):
        if true_count < 1:
            self.stake = min_bet
            print("BET:" + str(min_bet))
            self.initial_bet = min_bet
            self.bets[f'player {player_num + 1}'] = min_bet
            return min_bet
        else:
            self.stake = true_count * self.ABPTC
            print("BET:" + str(true_count * self.ABPTC))
            self.initial_bet = true_count * self.ABPTC
            self.bets[f'player {player_num + 1}'] = true_count * self.ABPTC
            return true_count * self.ABPTC

    def double(self, player_num):
        self.stake += self.initial_bet
        self.bets[f'player {player_num + 1}'] *= 2
        print("BETS_D: " + str(self.bets))


def basic_strategy(row, col):
    if col == 1:
        col = 11
    # print(row)
    # print(col)
    return int(BASIC_STRATEGY_TABLE[str(col)].loc[
                   BASIC_STRATEGY_TABLE['PNUM'] == str(row)].iloc[0])


class Card:
    card_values = {
        'two': 2,
        'three': 3,
        'four': 4,
        'five': 5,
        'six': 6,
        'seven': 7,
        'eight': 8,
        'nine': 9,
        'ten': 10,
        'jack': 10,
        'queen': 10,
        'king': 10,
        'ace': 11
    }

    def __init__(self, suit, value, face_up=True):
        self.suit = suit
        self.value = value
        self.numerical_value = self.card_values[value]
        self.face_up = face_up

    def set_ace_1(self):
        self.numerical_value = 1

    def set_face_down(self):
        self.face_up = False


class Table:
    burn_pile = []
    dealer_cards = []
    split_cards = {}
    initial_num_players = 0

    def __init__(self, num_players, num_decks):
        player_ABPTC = [20 for _ in range(num_players)]
        self.initial_num_players = num_players
        self.num_players = num_players
        self.num_decks = num_decks
        self.deck = Deck(num_decks)
        self.player_cards = {f'player {i + 1}': [] for i in range(num_players)}
        self.players = [Player(1000, abptc) for abptc in player_ABPTC]
        self.dealer_bankroll = 10000

    def deal_dealer(self, face_up=True):
        card = self.deck.draw(face_up)
        self.dealer_cards.append(card)
        print(str([card.numerical_value, card.suit]) + "DEALER")
        return card

    def deal_player(self, player_num):
        card = self.deck.draw()
        self.player_cards[f'player {player_num + 1}'].append(card)
        print(str([card.numerical_value, card.suit]) + " PLAYER NUM:" + str(player_num))

    def split(self, player_num, player):
        self.num_players += 1
        second_pair = self.player_cards[f'player {player_num + 1}'].pop()
        self.player_cards[f'player {len(self.player_cards) + 1}'] = list([second_pair])
        #print(str(self.split_cards))

        if f'player {player_num + 1}' in self.split_cards:
            root_player = self.split_cards[f'player {player_num + 1}']

            while root_player >= self.initial_num_players:
                root_player = self.split_cards[f'player {root_player + 1}']
            self.split_cards[f'player {len(self.player_cards)}'] = root_player
        else:
            self.split_cards[f'player {len(self.player_cards)}'] = player_num
        #print(str(self.split_cards))
        player.bet(0, 10, len(self.player_cards) - 1)
        return len(self.player_cards) - 1

    def get_hand_sums(self, player_num):
        if len(self.split_cards) >= 3:
            pass
        hand_sums = {}
        # print(str(self.split_cards))
        for key in self.split_cards:
            if self.split_cards[key] == player_num:
                hand_sums[int(key[-1]) - 1] = self.get_player_sum(int(key[-1]) - 1)
        return hand_sums

    def table_refresh(self, split=0):
        self.burn_pile.extend(self.dealer_cards)
        self.dealer_cards.clear()
        for i in range(self.num_players):
            # print("NP " + str(self.num_players))
            # print(str(self.player_cards))
            self.burn_pile.extend(self.player_cards[f'player {i + 1}'])
            self.player_cards[f'player {i + 1}'] = []
            # print(str(self.player_cards))
            # print("NP " + str(self.num_players))
        for _ in range(split):
            # print("#BOOM")
            player_num = len(self.player_cards)
            self.player_cards.pop(f'player {player_num}')
            self.num_players -= 1
        self.split_cards.clear()
        print("Burn Pile " + str(len(self.burn_pile)))

    def get_player_cards(self, player_num):
        return self.player_cards[f'player {player_num + 1}']

    def get_dealer_card(self):
        return self.dealer_cards[0]

    def get_dealer_cards(self):
        return self.dealer_cards

    def get_dealer_sum(self):  # TODO: implement H17 S17
        dealer_card_sum = 0
        for card in self.dealer_cards:
            dealer_card_sum += card.numerical_value
        return dealer_card_sum

    def get_player_sum(self, player_num):
        contains_ace = False
        player_card_sum = 0
        for card in self.get_player_cards(player_num):
            player_card_sum += card.numerical_value
        if player_card_sum > 21:
            for card in self.get_player_cards(player_num):
                if card.value == 'ace' and card.numerical_value == 11:
                    card.set_ace_1()
                    player_card_sum -= 10
                    if player_card_sum <= 21:
                        break
        return player_card_sum

    def dealer_bust(self):
        pass

    def player_bust(self, player_num):
        pass  # TODO: add check for ace


def play_round(table, num_players):
    for player_num in range(num_players):
        player = table.players[player_num]
        player.bet(0, 10, player_num)
        for i in range(2):
            table.deal_player(player_num)
        player_decision = player.make_decision(table, player_num)
        outcome = continue_round(table, player, player_num, player_decision)

        print("BANKROLL BEFORE: " + str(player.bankroll))
        if outcome == 1:
            if table.get_player_sum(player_num) == 21 and (len(table.get_player_cards(player_num)) == 2):
                player.win(player_num)
            else:
                player.win(player_num)
        elif outcome == 0:
            pass
        elif outcome == -1:
            player.lose(player_num)
        elif outcome == 2:
            player_sum = table.get_player_sum(player_num)
            dealer_sum = table.get_dealer_sum()
            if player_sum > 21:
                player.lose(player_num)
            elif dealer_sum > 21:
                player.win(player_num)
            elif player_sum > dealer_sum:
                player.win(player_num)
            else:
                player.lose(player_num)
            # player_sum = table.get_player_sum(table.num_players-1) #TODO: FIX ERROR HERE
            hand_sums = table.get_hand_sums(player_num)
            for split_player_num in hand_sums:
                if hand_sums[split_player_num] > 21:
                    player.lose(split_player_num)
                elif dealer_sum > 21:
                    player.win(split_player_num)
                elif hand_sums[split_player_num] > dealer_sum:
                    player.win(split_player_num)
                else:
                    player.lose(split_player_num)
        print("BANKROLL AFTER: " + str(player.bankroll))
    return outcome


def dealer_check_win(table, player_num):
    dealer_card_sum = table.get_dealer_sum()
    if dealer_card_sum > 21:
        for card in table.get_dealer_cards():
            if card.value == 'ace' and card.numerical_value == 11:
                card.set_ace_1()
                dealer_card_sum -= 10
                if dealer_card_sum <= 21:
                    break
    while dealer_card_sum < 17:
        new_card = table.deal_dealer()
        dealer_card_sum += new_card.numerical_value
        if dealer_card_sum > 21:
            for card in table.get_dealer_cards():
                if card.value == 'ace' and card.numerical_value == 11:
                    card.set_ace_1()
                    dealer_card_sum -= 10
                    if dealer_card_sum <= 21:
                        break
        if dealer_card_sum > 21:
            table.dealer_bust()
            return 1

    card_sum = table.get_player_sum(player_num)
    if card_sum > dealer_card_sum:
        return 1
    elif card_sum == dealer_card_sum:
        return 0
    else:
        return -1


def continue_round(table, player, player_num, player_decision):
    player_decision = int(player_decision)
    # assert(type(player_decision) == int)
    dealer_card = table.get_dealer_card()
    player_cards = table.get_player_cards(player_num)
    if player_decision == 1:
        table.deal_player(player_num)
        if table.get_player_sum(player_num) > 21:
            table.player_bust(player_num)  # TODO: check for ace
            return -1
        else:
            new_player_decision = player.make_decision(table, player_num)
            return continue_round(table, player, player_num, new_player_decision)
    elif player_decision == 2:
        rv = dealer_check_win(table, player_num)
        return rv
    elif player_decision == 3:
        split_player_num = table.split(player_num, player)
        table.deal_player(player_num)
        table.deal_player(split_player_num)
        new_player_decision = player.make_decision(table, player_num)
        split_player_decision = player.make_decision(table, split_player_num)
        continue_round(table, player, player_num, new_player_decision)
        continue_round(table, player, split_player_num, split_player_decision)
        split1_cards = table.get_player_cards(player_num)
        split2_cards = table.get_player_cards(split_player_num)
        print(f"SPLIT{player_num} CARDS")
        for card in split1_cards:
            print(str([card.numerical_value, card.suit]), end=" ")
            print("\n")
        print(f"SPLIT{split_player_num} CARDS")
        for card in split2_cards:
            print(str([card.numerical_value, card.suit]), end=" ")
            print("\n")
        return 2
    elif player_decision in [4, 5]:
        player.double(player_num)
        table.deal_player(player_num)
        if table.get_player_sum(player_num) > 21:
            table.player_bust(player_num)
            return -1
        else:
            return dealer_check_win(table, player_num)
    else:
        raise "Decision error"


def main():
    num_players = 1
    num_decks = 4
    for simulation_number in range(1000):
        table = Table(num_players, num_decks)
        for _ in range(100):
            while table.deck.cards_remaining > 70:
                print("REMAINING CARDS IN DECK: " + str(table.deck.cards_remaining))
                table.deal_dealer()
                table.deal_dealer(face_up=False)
                print("\nDEALER CARDS")
                dealer_cards = table.get_dealer_cards()
                for card in dealer_cards:
                    if card.face_up:
                        print(str([card.numerical_value, card.suit]))
                print("\n")

                print("PLAYER CARDS")
                outcome = play_round(table, num_players)
                print("Dealer sum: " + str(table.get_dealer_sum()))
                print("Outcome: " + str(outcome))
                print("PLAYER BANKROLL " + str(table.players[0].bankroll))
                print(table.deck.cards_remaining)
                print("***********************************************************************************\n")
                if outcome == 2:
                    split = len(table.get_hand_sums(0))  # for now
                else:
                    split = 0
                table.table_refresh(split)
            table.deck.reshuffle()


if __name__ == "__main__":
    main()
