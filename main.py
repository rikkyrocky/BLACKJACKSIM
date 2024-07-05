# Credit for basic strategy CSV goes to: https://github.com/RochesterinNYC/BlackjackStrategyTester
import random
import pandas as pd
import time

BASIC_STRATEGY_TABLE = pd.read_csv('rsc/blackjackstrategychart.csv')

class Deck:
    count = 0

    def __init__(self, num_decks):
        suits = ['hearts', 'diamonds', 'clubs', 'spades']
        values = ['two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'jack', 'queen', 'king',
                  'ace']
        self.cards = [Card(suit, value) for _ in range(num_decks) for suit in suits for value in values]
        self.cards_remaining = 52 * num_decks

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
    def __init__(self, bankroll, ABPTC): # ABPTC = additional bet per true count
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

    def win(self, value):
        self.stake =0
        self.bankroll += value
    def lose(self, value):
        self.stake = 0
        self.bankroll -= value
    def bet(self, true_count, min_bet):
        if true_count < 1:
            self.stake = min_bet
            return min_bet
        else:
            self.stake = true_count * self.ABPTC
            return true_count * self.ABPTC


def basic_strategy(row, col):
    #print(row)
    #print(col)
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

    def __init__(self, num_players, num_decks):
        player_ABPTC = [20 for _ in range(num_players)]
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
        print(str([card.numerical_value, card.suit]) + "PLAYER")

    def split(self, player_num):
        self.num_players += 1
        second_pair = self.player_cards[f'player {player_num + 1}'].pop()
        self.player_cards[f'player {len(self.player_cards) + 1}'] = list([second_pair])
        return len(self.player_cards) - 1


    def table_refresh(self, split=0):
        self.burn_pile.extend(self.dealer_cards)
        self.dealer_cards.clear()
        for i in range(self.num_players):
            self.burn_pile.extend(self.player_cards[f'player {i + 1}'])
            self.player_cards[f'player {i + 1}'] = []
        for _ in range(split):
            player_num = len(self.player_cards)
            self.player_cards.pop(f'player {player_num}')
        print("Burn Pile " + str(len(self.burn_pile)))

    def get_player_cards(self, player_num):
        return self.player_cards[f'player {player_num + 1}']

    def get_dealer_card(self):
        return self.dealer_cards[0]

    def get_dealer_cards(self):
        return self.dealer_cards

    def get_dealer_sum(self): #TODO: implement H17 S17
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
        pass # TODO: add check for ace

def play_round(table, num_players):
    for player_num in range(num_players):
        player = table.players[player_num]
        player.bet(0, 10)
        for i in range(2):
            table.deal_player(player_num)
        player_decision = player.make_decision(table, player_num)
        outcome = continue_round(table, player, player_num, player_decision)

        if outcome == 1:
            if table.get_player_sum(player_num) == 21:
                player.win(player.stake * 1.5)
            else:
                player.win(player.stake)
        elif outcome == 0:
            pass
        elif outcome == -1:
            player.lose(player.stake)
        elif outcome == 2:
            player_sum = table.get_player_sum(player_num)
            dealer_sum = table.get_dealer_sum()
            if player_sum > 21:
                player.lose(player.stake)
            elif dealer_sum > 21:
                player.win(player.stake)
            elif player_sum > dealer_sum:
                player.win(player.stake)
            else:
                player.lose(player.stake)
            player_sum = table.get_player_sum(len(table.player_cards)) #TODO: FIX ERROR HERE
            if player_sum > 21:
                player.lose(player.stake)
            elif dealer_sum > 21:
                player.win(player.stake)
            elif player_sum > dealer_sum:
                player.win(player.stake)
            else:
                player.lose(player.stake)
    return outcome



def dealer_check_win(table, player_num):
    print("###")
    dealer_card_sum = table.get_dealer_sum()
    print("log0 " + str(dealer_card_sum))
    while dealer_card_sum < 17:
        print("log1 " + str(dealer_card_sum))
        new_card = table.deal_dealer()
        dealer_card_sum += new_card.numerical_value
    if dealer_card_sum > 21:
        table.dealer_bust()
        return 1

    card_sum = table.get_player_sum(player_num)
    print("LOG2:" + " " + str(card_sum) + " " + str(dealer_card_sum))
    if card_sum > dealer_card_sum:
        return 1
    elif card_sum == dealer_card_sum:
        return 0
    else:
        return -1




def continue_round(table, player, player_num, player_decision):
    player_decision = int(player_decision)
    #assert(type(player_decision) == int)
    dealer_card = table.get_dealer_card()
    player_cards = table.get_player_cards(player_num)
    if player_decision == 1:
        table.deal_player(player_num)
        if table.get_player_sum(player_num) > 21:
            table.player_bust(player_num) #TODO: check for ace
            return -1
        else:
            new_player_decision = player.make_decision(table, player_num)
            return continue_round(table, player, player_num, new_player_decision)
    elif player_decision == 2:
        rv = dealer_check_win(table, player_num)
        return rv
    elif player_decision == 3:
        split_player_num = table.split(player_num)
        table.deal_player(player_num)
        table.deal_player(split_player_num)
        new_player_decision = player.make_decision(table, player_num)
        split_player_decision = player.make_decision(table, split_player_num)
        continue_round(table, player, player_num, new_player_decision)
        continue_round(table, player, split_player_num, split_player_decision)
        split1_cards = table.get_player_cards(player_num)
        split2_cards = table.get_player_cards(split_player_num)
        print("SPLIT1 CARDS")
        for card in split1_cards:
            print(str([card.numerical_value, card.suit])) #TODO: might be easier to do payouts here
        print("SPLIT2 CARDS")
        for card in split2_cards:
            print(str([card.numerical_value, card.suit]))
        return 2
    elif player_decision in [4, 5]:
        player.stake = player.stake*2
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
    table = Table(num_players, num_decks)
    while table.deck.cards_remaining > 10:
        print(table.deck.cards_remaining)
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
            split = 1
        else:
            split = 0
        table.table_refresh(split)


if __name__ == "__main__":
    main()
