"""
project info:
    project_name = Splendor
    programmer   = Varisox137
    code_version = 23.3.8
"""
from random import shuffle,sample
from time import sleep
import turtle

# throughout this project, the order of 5 colors should be: WHite,BlacK,ReD,GReen,BLue
COLORS=['WH','BK','RD','GR','BL']
COLORX=COLORS+['GD']
TOKENS={'WH':0,'BK':0,'RD':0,'GR':0,'BL':0,'GD':5}

HINT5=' (1~5 for white,black,red,green,blue)'
HINT6=' (1~6 for white,black,red,green,blue,gold)'

DECK=[
      [],[],[]
] # of card level 1,2 and 3
NOBLES=[] # of up to 3~5 noble tiles

def _l2d(l:list):
    assert 5<=len(l)<=6,'ListLengthError_L2D'
    d=dict()
    for i in range(len(l)):
        d[(COLORS if len(l)==5 else COLORX)[i]]=l[i]
    return d

class Card:
    def __init__(self,l:int,s:int,c:str,costs:[int]):
        self.level=l
        self.score=s
        self.color=c
        self.costs=_l2d(costs)
        
    def disp(self):
        print('Level:',self.level,'  Color:',self.color,'  Score:',self.score,'\nCosts:',self.costs)

class Noble:
    def __init__(self,req:[int]):
        self.score=3
        self.reqs=_l2d(req)
        
    def disp(self):
        print('Score:',self.score,'\nRequirements:',self.reqs)

class Player:
    def __init__(self):
        self.score=0
        self.cards=_l2d([[],[],[],[],[]])
        self.tokens=_l2d([0,0,0,0,0,0])
        self.preserved_cards=[]
        self.nobles=[]
    
    def trial(self,command:str):
        def _prompt(command):
            if command=='return_tokens':
                s=input('\nInput tokens to return'+HINT6+': ')
                assert (s.isdigit() and len(s)==sum(self.tokens)-10 and
                	all(1<=int(s[n])<=6 for n in range(len(s)))),'InputError'
                s=list(map(int,list(s)))
                data=[0,0,0,0,0,0]
                for k in s: data[k-1]+=1
            elif command=='get_tokens':
                s=input('\nInput tokens to get'+HINT5+': ')
                assert (s in ['1','2','3','4','5',
                              '11','12','13','14','15','22','23','24','25','33','34','35','44','45','55',
                              '123','124','125','134','135','145','234','235','245','345']),'InputError'
                s=list(map(int,list(s)))
                data=[0,0,0,0,0]
                for k in s: data[k-1]+=1
            elif command.endswith('card'):
                if command=='buy_card':
                    s=input('\nChoose card to buy (input Slot Number 1~12, or 13~15 for preserved cards): ')
                else:
                    s=input('\nChoose card to preserve (input Slot Number 1~12): ')
                assert s.isdigit(),'InputError'
                s=int(s)
                assert (1<=s<=12 and (data:=TABLE[(s-1)//4][(s-1)%4])) or (13<=s<=15 and s-12<=len(self.preserved_cards) and (data:=self.preserved_cards[s-13])),'InputError'
                return [[(s-1)//4,(s-1)%4] if s<=12 else s-12,data]
            elif command=='check_noble':
                return [[],[len(self.cards[color]) for color in COLORS]]
            
            return [[],data]
        
        data=_prompt(command)
        pos,data=data[0],data[1]
        exec('self._'+command+'(data)')
        if pos in [1,2,3]: self.preserved_cards.pop(pos-1)
        elif isinstance(pos,list) and len(pos)==2: TABLE[pos[0]][pos[1]]=None
    
    def _return_tokens(self,amounts:[int]): # should have len(amounts)==6
        assert len(amounts)==6,'ListLengthError_Rtn'
        amounts=_l2d(amounts)
        if all([(self.tokens[color]>=amounts[color]) for color in COLORX]):
            for color in COLORX:
                self.tokens[color]-=amounts[color]
        else: # don't have enough token at hand to return
            assert False,'NotEnoughTokensToReturn'
    
    def _get_tokens(self,amounts:[int]):
        assert len(amounts)==5,'ListLengthError_Get'
        amounts=_l2d(amounts)
        for color in COLORS:
            assert (amounts[color]<=1 or (amounts[color]==sum(amounts.values())==2 and TOKENS[color]>=4)),'TokenAmountError'
        if all([(TOKENS[color]>=amounts[color]) for color in COLORS]):
            for color in COLORS:
                TOKENS[color]-=amounts[color]
                self.tokens[color]+=amounts[color]
        else: # cannot get enough tokens from bank
            raise AssertionError('NotEnoughTokensInBank')
        if sum(self.tokens.values())>10:
            self.trial('return_tokens')
    
    def _buy_card(self,card): # card.costs=[int*5]
        real_costs=_l2d([0,0,0,0,0,0])
        for color in COLORS:
            real_costs[color]=max(0,card.costs[color]-len(self.cards[color]))
            real_costs['GD']+=(d:=max(0,real_costs[color]-self.tokens[color]))
            real_costs[color]-=d
        if all([(self.tokens[color]>=real_costs[color]) for color in COLORX]):
            # first, spend tokens in hand and buy
            # next, return tokens to bank
            for color in COLORX:
                self.tokens[color]-=real_costs[color]
                TOKENS[color]+=real_costs[color]
            self.cards[card.color].append(card)
            self.score+=card.score
        else: # cannot pay enough tokens
            raise AssertionError('NotEnoughTokensToPurchase')
    
    def _preserve_card(self,card):
        assert len(self.preserved_cards)<3,'CannotPreserve3+'
        self.preserved_cards.append(card)
        if TOKENS['GD']>0: TOKENS['GD']-=1;self.tokens['GD']+=1
        if sum(self.tokens.values())>10:
            self.trial('return_tokens')
            
    def _check_noble(self,req:[int]):
        print('\n-----  Noble check  -----')
        avail=[]
        for each in NOBLES:
            if all([(len(self.cards[color])>=each.reqs[color]) for color in COLORS]):
                avail.append(each)
        if avail:
            print('Available nobles(s):')
            for i in range(len(avail)):
                print('\n',i+1)
                avail[i].disp()
            while True:
                s=input('Choose a noble to receive:')
        else:
            print('None are available.')
        
def show_table():
    print('\n----------   CURRENT TABLETOP   ----------'); sleep(0.7)
    print('\n-----  Cards  -----'); sleep(0.7)
    for level in range(3):
        print('\n** Level',3-level); sleep(0.5)
        for pos in range(4):
            print('\nSlot',(2-level)*4+pos+1)
            if card:=TABLE[2-level][pos]: card.disp()
            else: print('Empty.')
            sleep(0.3)
    print('\n-----  Tokens  -----\n',TOKENS)
    sleep(0.7)
        
def fill_shop():
    for level in range(3):
        for pos in range(4):
            if (TABLE[level][pos] is None) and DECK[level]:
                TABLE[level][pos]=DECK[level].pop()

TABLE=[[None for _ in range(4)] for _ in range(3)]

DECK[0]=[ # card level 1
    Card(1,1,'WH',[0,0,0,4,0]), Card(1,0,'WH',[0,1,2,0,0]),
    Card(1,1,'BK',[0,0,0,0,4]), Card(1,0,'BK',[0,0,1,2,0]),
    Card(1,1,'RD',[4,0,0,0,0]), Card(1,0,'RD',[0,0,0,1,2]),
    Card(1,1,'GR',[0,4,0,0,0]), Card(1,0,'GR',[2,0,0,0,1]),
    Card(1,1,'BL',[0,0,4,0,0]), Card(1,0,'BL',[1,2,0,0,0]),

    Card(1,0,'WH',[0,0,0,0,3]), Card(1,0,'WH',[0,1,1,1,1]), Card(1,0,'WH',[0,2,0,0,2]),
    Card(1,0,'BK',[0,0,0,3,0]), Card(1,0,'BK',[1,0,1,1,1]), Card(1,0,'BK',[2,0,0,2,0]),
    Card(1,0,'RD',[3,0,0,0,0]), Card(1,0,'RD',[1,1,0,1,1]), Card(1,0,'RD',[2,0,2,0,0]),
    Card(1,0,'GR',[0,0,3,0,0]), Card(1,0,'GR',[1,1,1,0,1]), Card(1,0,'GR',[0,0,2,0,2]),
    Card(1,0,'BL',[0,3,0,0,0]), Card(1,0,'BL',[1,1,1,1,0]), Card(1,0,'BL',[0,2,0,2,0]),

    Card(1,0,'WH',[0,1,1,2,1]), Card(1,0,'WH',[0,1,0,2,2]), Card(1,0,'WH',[3,1,0,0,1]),
    Card(1,0,'BK',[1,0,1,1,2]), Card(1,0,'BK',[2,0,1,0,2]), Card(1,0,'BK',[0,1,3,1,0]),
    Card(1,0,'RD',[2,1,0,1,1]), Card(1,0,'RD',[2,2,0,1,0]), Card(1,0,'RD',[1,3,1,0,0]),
    Card(1,0,'GR',[1,2,1,0,1]), Card(1,0,'GR',[0,2,2,0,1]), Card(1,0,'GR',[1,0,0,1,3]),
    Card(1,0,'BL',[1,1,2,1,0]), Card(1,0,'BL',[1,0,2,2,0]), Card(1,0,'BL',[0,0,1,3,1])
]

DECK[1]=[ # card level 2
    Card(2,2,'WH',[0,0,5,0,0]), Card(2,3,'WH',[6,0,0,0,0]), Card(2,2,'WH',[0,2,4,1,0]),
    Card(2,2,'BK',[5,0,0,0,0]), Card(2,3,'BK',[0,6,0,0,0]), Card(2,2,'BK',[0,0,2,4,1]),
    Card(2,2,'RD',[0,5,0,0,0]), Card(2,3,'RD',[0,0,6,0,0]), Card(2,2,'RD',[1,0,0,2,4]),
    Card(2,2,'GR',[0,0,0,5,0]), Card(2,3,'GR',[0,0,0,6,0]), Card(2,2,'GR',[4,1,0,0,2]),
    Card(2,2,'BL',[0,0,0,0,5]), Card(2,3,'BL',[0,0,0,0,6]), Card(2,2,'BL',[2,4,1,0,0]),

    Card(2,1,'WH',[0,2,2,3,0]),
    Card(2,1,'BK',[3,0,0,2,2]),
    Card(2,1,'RD',[3,2,2,0,0]),
    Card(2,1,'GR',[2,2,0,0,3]),
    Card(2,1,'BL',[0,0,3,2,2]),

    Card(2,1,'WH',[2,0,3,0,3]), Card(2,2,'WH',[0,3,5,0,0]),
    Card(2,1,'BK',[3,2,0,3,0]), Card(2,2,'BK',[0,0,3,5,0]),
    Card(2,1,'RD',[0,3,2,0,3]), Card(2,2,'RD',[3,5,0,0,0]),
    Card(2,1,'GR',[3,0,3,2,0]), Card(2,2,'GR',[0,0,0,3,5]),
    Card(2,1,'BL',[0,3,0,3,2]), Card(2,2,'BL',[5,0,0,0,3])
]

DECK[2]=[ # card level 3
    Card(3,4,'WH',[0,7,0,0,0]), Card(3,5,'WH',[3,7,0,0,0]),
    Card(3,4,'BK',[0,0,7,0,0]), Card(3,5,'BK',[0,3,7,0,0]),
    Card(3,4,'RD',[0,0,0,7,0]), Card(3,5,'RD',[0,0,3,7,0]),
    Card(3,4,'GR',[0,0,0,0,7]), Card(3,5,'GR',[0,0,0,3,7]),
    Card(3,4,'BL',[7,0,0,0,0]), Card(3,5,'BL',[7,0,0,0,3]),

    Card(3,4,'WH',[3,6,3,0,0]), Card(3,3,'WH',[0,3,5,3,3]),
    Card(3,4,'BK',[0,3,6,3,0]), Card(3,3,'BK',[3,0,3,5,3]),
    Card(3,4,'RD',[0,0,3,6,3]), Card(3,3,'RD',[3,3,0,3,5]),
    Card(3,4,'GR',[3,0,0,3,6]), Card(3,3,'GR',[5,3,3,0,3]),
    Card(3,4,'BL',[6,3,0,0,3]), Card(3,3,'BL',[3,5,3,3,0])
]

NOBLES=[
    Noble([4,4,0,0,0]), Noble([0,4,4,0,0]), Noble([0,0,4,4,0]), Noble([0,0,0,4,4]), Noble([4,0,0,0,4]),
    Noble([3,3,3,0,0]), Noble([0,3,3,3,0]), Noble([0,0,3,3,3]), Noble([3,0,0,3,3]), Noble([3,3,0,0,3])
]

def init_turtle():
    turtle.screensize(1080,720)
    turtle.setup(1280,780,0,0)
    turtle.pensize(1)
    turtle.speed(10)
    turtle.penup()
    turtle.hideturtle()
    turtle.clear()

def draw_rect(x0,y0,dx,dy): # slot 1~12
    turtle.setx(x0); turtle.sety(y0)
    turtle.setheading(0)
    turtle.pendown()
    for _ in range(2):
        turtle.forward(dx); turtle.right(90)
        turtle.forward(dy); turtle.right(90)
    turtle.penup()

CARD_SIZE=[105, 150]

def draw_card(slot:int,c:(Card|None)):
    x0=((slot-1)%4)*135-335
    y0=((slot-1)//4)*180-60
    draw_rect(x0,y0,CARD_SIZE[0],CARD_SIZE[1])
    if c is None:
        turtle.setx(x0+30)
        turtle.sety(y0-60)
        turtle.setheading(0)
        turtle.write('Empty.',font=('Arial',8,'normal'))
    else:
        turtle.setx(x0+32)
        turtle.sety(y0-84)
        turtle.setheading(0)
        turtle.write('Empty.',font=('Arial',12,'normal'))

def draw_noble(n:Noble):
    pass

def draw_token(t:str):
    assert t in TOKENS,'TokenTypeError'
    pass

def init_table():
    for slot_y in range(3):
        for slot_x in range(5):
            if slot_x!=0: draw_card(slot_y*4+slot_x,TABLE[slot_y][slot_x-1])
            else:
                draw_rect(-480,slot_y*180-60,CARD_SIZE[0],CARD_SIZE[1])

def game_main():
    global NOBLES
    print('\n----------   Game start! Setup:   ----------')
    while k:=input('\nPlayer number ?= '):
        if k.isdigit() and 2<=(k:=int(k))<=4:
            break
        else: print('Wrong input !')
    for color in COLORS: TOKENS[color]=[0,0,4,5,7][k]
    for i in range(3): shuffle(DECK[i])
    fill_shop()
    players=[Player() for _ in range(k)]
    NOBLES=sample(NOBLES,k+1)

    if __name__=='__main__':
        init_turtle()
        init_table()
        turtle.exitonclick()
        input()

    turn=[False, 0]
    while not turn[0]:
        turn[1]+=1
        print('\n*****  ROUND',turn[1],' *****')
        for pid in range(k):
            print("\n----------   Now it's Player "+str(pid+1)+'   ----------')
            if turn[0]: print('***  FINAL TURN !  ***')
            p=players[pid]
            show_table()
            print('\n---  Your assets  ---'); sleep(0.7)
            print('* Score:\n',p.score)
            print('* Cards:\n',_l2d([len(p.cards[color]) for color in COLORS]))
            print('* Tokens:\n',p.tokens)
            sleep(0.7)
            while True:
                c=input('\nYour action (1=get tokens, 2=buy card, 3=preserve card) ?= ')
                if not (c.isdigit() and 1<=(c:=int(c))<=3):
                    print('wrong input !')
                    continue
                try:
                    if c==1: p.trial('get_tokens')
                    elif c==2: p.trial('buy_card')
                    else: p.trial('preserve_card')
                    break
                except AssertionError as e:
                    from traceback import print_exc
                    print_exc()
                    sleep(1)
                    continue
            fill_shop()
            p.trial('check_noble')
            if p.score>=15:
                print('\nYou reach 15 prestige points!\nGame will end after this turn.')
                turn[0]=True
    winner=[0,0]
    for n in range(k):
        if (p:=players[k]).score>winner[1]: winner=[k+1,p.score]
    print('\nGame ends! Player',winner[0],'wins with',winner[1],'points!')
    input()

if __name__=='__main__':
    game_main()