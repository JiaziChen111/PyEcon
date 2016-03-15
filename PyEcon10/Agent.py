# -*- coding: utf-8 -*-
# Agent.py
from scipy import *
import pandas as pd
import scipy.stats as stats
from Tools import *
import pickle




# Exogenouse phisical environment = World / Field #####################

Ns = 1 # Number of fictions
Nh = 100 #1000 # Number of households
Nf = Nh/10 #100 # Number of firms # Actual = 7.6% to LF
Days = 21 # Working days in a month
Months = 3000 # Months for simulation


#######################################################################




class SCRIPT:
    def __init__(self,ID):

        self.ID = ID

        # /// Firms ///
        # Wage setting
        self.SHmax = 24 # Maximum successfull hiring months for wage downgrade
        self.sig = 0.019 # support for random wage revision rate


        # Labor adjustment
        self.UR_0 = 0.0 # Initial unemployment rate

        self.phimax = 1.0 # maximum inventry to demand ratio for firing
        self.phimin = 0.25 # minimum inventry to demand ratio for hiring
        self.Lmin = 0 # minimum labor size to keep searchable by hh

        # Goods price setting
        self.psimax = 0.5  # maximum demand gap for price hiking
        self.psimin = -0.7 # minimum demand gap for price cutting
        self.nu = 0.01 # price revision rate
        self.theta = 0.75 # Calvo probability to change price

        # Production
        self.lamb = 1.0/Days # production function coef (technology) on L, >0.


        # /// Households ///
        # Labor maket search
        self.beta = 0.4*Nf # maximum employer search for an unemployed hh
        self.pi_vis = 0.1 # probability for satisfied hh to visit a new firm
        self.down_Wh = 0.2 # discout rate of researvation wage when unemp

        # Consumption
        self.Ahmax = 0.3*Nf #Maximum connection from HH to FI for consumption
        self.nmax = 0.3*Nf # maximun repetation of shopping visit <=Ahmax
        self.xi = 0.01   # price threshold to replace fi
        self.xi_q = 0.25 # probability for hh to pick a candidate fi
        self.xi_p = 0.25 # probability for hh to pick a candidate fi
        self.alpha = 0.9 # decaying rate of consumption function
        self.sati_max = 0.95 # acceptable satisfaction rate for shopping



# インタラクションの際は、アクションの順番がID順にならないように、リストのシャッフルが必要。そのためにも、要素の選択は、リストのインデックスではく、IDの照合で行うこと。



    def story(self, hh_set, fi_set):
        # /// Start of a month ///

        # Independent fi actions
        shuffle(fi_set)
        for fi in fi_set:
            fi.Wf_set()
            fi.Fire(hh_set)
            fi.checkB(hh_set)
            fi.L_set()
            fi.P_set()
            fi.reset_flow()

        # Independent hh actions
        shuffle(hh_set)
        for hh in hh_set:
            hh.searchA(fi_set)
            hh.searchB(fi_set)
            hh.C_plan()


        # /// Days ///
        Today = 1
        while Today <= Days:

            # Independent hh actions
            shuffle(hh_set)
            for hh in hh_set:
                hh.consumption(fi_set)

            # Independent fi actions
            shuffle(fi_set)
            for fi in fi_set:
                fi.production()

            Today += 1



        # /// End of a month ///
        # Independent fi actions
        shuffle(fi_set)
        for fi in fi_set:
            fi.pay(hh_set)

        # Independent hh actions
        shuffle(hh_set)
        for hh in hh_set:
            hh.Wh_set(fi_set)



class FI:
    def __init__(self, ID, intSVf=None):

        # Agent
        self.ID = ID

        # Preset state variables
        self.Wf = 1. ## Wage = Marginal cost
        self.Mf = 1. ## Monery
        self.Pf = 1. # Price
        self.Y = 1. # Production

        self.SH = 1 # Successful hiring months
        self.D_old = 1. # Demands during the last month
        self.Inv = 1. # Current inventories
        self.OP= 1 # Open position
        self.fireID = None

        # Network
        self.Bf = None # Employees



    def Wf_set(self):
        """
        Set Wage accoding to the hiring history.
        """
        mu = AS.sig*rand()

        if self.SH > AS.SHmax:
            self.Wf = self.Wf*(1.-mu)

        elif self.SH==0:
            self.Wf = self.Wf*(1.+mu)




    def Fire(self,hh_set):
        """
        Fire the assigned hh last month at the start of month.
        """
        if self.fireID != None:
            for i in range(len(self.fireID)):
                self.Bf.remove(self.fireID[i])
                hh_set[ID_ind(hh_set, self.fireID[i])].Bh = None

            self.fireID = None



    def checkB(self,hh_set):
        """
        Understand each employee and labor input.
        """
        self.Bf=[]
        for i in range(Nh):
            if hh_set[i].Bh == self.ID:
                self.Bf.append(hh_set[i].ID)
        self.L = len(self.Bf)




    def L_set(self):
        """
        Adjust labor input and price according to the inventory last month and marginal cost (layered adjustment).
        """
        # Count successful hiring

        if self.OP == 0:
            self.SH +=1
        else:
            self.SH = 0

        # Inventory controll
        Invmax=AS.phimax*self.D_old
        Invmin=AS.phimin*self.D_old

        if self.Inv < Invmin: # if supply shorted last month
            #shL = int((Invmin - self.Inv)/(AS.lamb)) # labor shortage
            self.OP += 1 #shL # 1 #

        elif self.Inv > Invmax: # if supply excessed last month
            if len(self.Bf) > AS.Lmin:
                # exL = int((self.Inv - Invmax)/(AS.lamb)) # Excess labor
                redH= 1 # min(exL,len(self.Bf))#  # Headcount reductions
                Bf_ = list(copy(self.Bf)) # to keep self.Bf unchange
                self.fireID = empty(redH) # Receptor
                for i in range(redH):
                    self.fireID[i] = Bf_.pop(randint(len(Bf_))) # randomly pick redH to fire



    def P_set(self):
        """
        Price adjustment according to demand gap
        """
        # Demand gap
        D_gap = self.D_old - (self.Y + self.Inv)

        # Price up
        if D_gap/self.Inv > AS.psimax:
            self.Pf = self.Pf*(1+AS.nu*D_gap)

        # Price down
        elif D_gap/self.Inv < AS.psimin: # and self.Pf >= self.Wf:
            self.Pf = self.Pf*(1+AS.nu*D_gap)



    def reset_flow(self):
        """
        Reset Y and D_old as those are flow measures
        """
        self.Y = 0
        self.D_old = 0


    def production(self):
        """
        Daily production.
        """
        self.L = len(self.Bf)
        prod_today = AS.lamb * self.L # production function
        self.Inv += prod_today
        self.Y += prod_today


    def pay(self, hh_set):
        """
        Wage payment and other clearance.
        """

        # Household asset situation
        hhAl =array([hh_set[i].Mh for i in range(len(hh_set))])
        hhA = hhAl.sum() # total household asset
        hhAd = hhAl/hhA # household asset distribution
        #hhAd = ones(Nh)/Nh # use when distribute evenly

        for hi in self.Bf:
            hhID = ID_ind(hh_set,hi)
            hh_set[hhID].Mh += self.Wf
            self.Mf -= self.Wf


        # Distribute positive dividents / negative dividents (bailout);
        net_div = self.Mf
        for i in range(len(hh_set)):
            hh_set[i].Mh += net_div * hhAd[i]
            self.Mf -= net_div * hhAd[i]






class HH:
    def __init__(self, ID, intSVh=None):

        # Agent
        self.ID = ID

        # State variables
        self.Wh = 1 ## Reservation wage
        self.Mh = 1 ## Monery


        # Network
        self.Ah = randint(Nf,size=AS.Ahmax) # Following shops
        self.Bh = randint(Nf)  # Belonging shop
        if random.binomial(1,AS.UR_0) == 1:
            self.Bh = None

        self.shortS = zeros(len(self.Ah)) # Remember short supply of following shops last month





    def searchA(self, fi_set):
        """
        Replace a failed shop to new one and then, to a cheaper shop with some advantatge of familiality
        """

        # Relace follows depend on supply failure
        if random.binomial(1,AS.xi_q):
            repIDs = []
            for i in range(len(self.Ah)):
                 repIDs = repIDs + list(repeat(self.Ah[i],int(self.shortS[i])))
            if len(repIDs) > 0:
                repID = repIDs[randint(len(repIDs))]
                self.Ah[self.Ah==repID] = randint(Nf)
                self.shortS = zeros(len(self.Ah))  # reset shortS when Ah changed

        # Relace follows to better price
        if random.binomial(1,AS.xi_p):
            repID = self.Ah[randint(len(self.Ah))]
            comIDs = []
            for fi in fi_set:
                comIDs = comIDs + list(repeat(fi.ID,max(len(fi.Bf),1))) # pick up probability depend on firm size
            #comIDs = range(Nf)# equal opotunities
            comID = comIDs[randint(len(comIDs))]

            if ID_pick(fi_set,comID).Pf < (1 - AS.xi)*ID_pick(fi_set,repID).Pf:
                self.Ah[self.Ah==repID] = comID



    def searchB(self, fi_set):
        """
        Labor maket search.
        """
        effort = 0
        # If unemployed, visit a firm to check open position repeatedly
        if self.Bh == None:
            while effort <= AS.beta:
                visID = randint(Nf); effort += 1
                if ID_pick(fi_set,visID).Wf >= self.Wh and ID_pick(fi_set,visID).OP > 0:
                    self.Bh = visID
                    fi_set[ID_ind(fi_set,visID)].OP -= 1

        # If satisfied, ramdomly visit another firm
        elif ID_pick(fi_set,self.Bh).Wf >= self.Wh and random.binomial(1,AS.pi_vis):
            visID = randint(Nf)
            if ID_pick(fi_set,visID).Wf >= self.Wh and ID_pick(fi_set,visID).OP > 0 and ID_pick(fi_set,self.Bh).L > AS.Lmin:
                    self.Bh = visID
                    fi_set[ID_ind(fi_set,visID)].OP -= 1

        # If unsatisfied, decisively visit another firm
        elif ID_pick(fi_set,self.Bh).Wf < self.Wh:
            visID = randint(Nf)
            if ID_pick(fi_set,visID).Wf >= self.Wh and ID_pick(fi_set,visID).OP > 0 and ID_pick(fi_set,self.Bh).L > AS.Lmin:
                    self.Bh = visID
                    fi_set[ID_ind(fi_set,visID)].OP -= 1


    def C_plan(self):
        """
        Monthly consumption planning based on the latest real income.
        """
        self.Ph = average([ID_pick(fi_set,i).Pf for i in self.Ah])
        income = max(self.Mh,0)
        self.Cmon = min((income/self.Ph)**AS.alpha, income/self.Ph)



    def consumption(self, fi_set):
        """
        Consumption transaction.
        """

        sati = 0.
        visin= 0
        planed = self.Cmon/Days

        while sati <= AS.sati_max and visin <= AS.nmax:
            iah = randint(AS.Ahmax) ; visin+=1
            visind = ID_ind(fi_set,self.Ah[iah])
            demand = planed * (1.-sati) # demand is set as a remaining
            expend = fi_set[visind].Pf * demand

            # Enough inventories and hh afordable
            if fi_set[visind].Inv >= demand and self.Mh >= expend:
                self.Mh -= expend # hh purchase
                fi_set[visind].Mf += expend # fi sales
                fi_set[visind].Inv -= demand # fi inv stock
                fi_set[visind].D_old += demand # fi remember demand
                sati += demand/planed


            # in case hh unafordable
            elif self.Mh < expend:
                maxbuy = self.Mh/fi_set[visind].Pf # maximum affordable demand
                self.Mh -= self.Mh # spend all money
                fi_set[visind].Mf += self.Mh # fi sales
                fi_set[visind].Inv -= maxbuy
                fi_set[visind].D_old += maxbuy # fi remember demand
                sati += maxbuy/planed


            # in case fi inventory shortage
            elif fi_set[visind].Inv < demand:
                maxsell = fi_set[visind].Inv # maximum inventory

                self.Mh -= fi_set[visind].Pf * maxsell # hh purchase
                fi_set[visind].Mf += fi_set[visind].Pf * maxsell # fi sales
                fi_set[visind].Inv -= maxsell # sell all inventory
                fi_set[visind].D_old += demand # fi remember demand
                sati += maxsell/planed

                # hh remember supply shortage
                self.shortS[iah] += demand - maxsell

        self.Dunc = planed*(1.-sati)



    def Wh_set(self, fi_set):
        """
        Researvation wage adjustmenet.
        """
        if self.Bh == None:
            self.Wh = (1.-AS.down_Wh) * self.Wh

        else:
            wage = ID_pick(fi_set,self.Bh).Wf
            if  wage > self.Wh:
                self.Wh = wage









# Actualization ##########################################################
AS = SCRIPT(0) # Actualized Script

hh_set = [HH(i) for i in range(Nh)]
fi_set = [FI(i) for i in range(Nf)]

# /// Run simulation ///
month = 1
states=['Mh','Cmon','Dunc','Inv','L','OP','Wf','Pf','Y']



Data = pd.DataFrame(index=range(month,Months),columns=states)


while month <= Months:
    # Play
    AS.story(hh_set, fi_set)

    # Save
    Data.Mh[month] = array([hh_set[i].Mh for i in range(Nh)])
    Data.Cmon[month] = array([hh_set[i].Cmon for i in range(Nh)])
    Data.Dunc[month] = array([hh_set[i].Dunc for i in range(Nh)])
    Data.Inv[month] = array([fi_set[i].Inv for i in range(Nf)])
    Data.L[month] = array([fi_set[i].L for i in range(Nf)])
    Data.OP[month] = array([fi_set[i].OP for i in range(Nf)])
    Data.Wf[month] = array([fi_set[i].Wf for i in range(Nf)])
    Data.Pf[month] = array([fi_set[i].Pf for i in range(Nf)])
    Data.Y[month] = array([fi_set[i].Y for i in range(Nf)])



    print round(float(month) / Months*100,1)
    month += 1



# /// Result ///

# Pxx, freqs, bins, im = specgram(detrend(Data_agr(Data,['Y'],how='sum').values.flatten()), NFFT = 256, Fs = 1, window=hamming(256))


# hist(Data.Mh[Months])
# hist(Data.L[Months])
# Data_agr(Data,['Y','Cmon','Inv','L','OP'],how='sum').plot()
# (100-Data_agr(Data,['L'],how='sum')).plot()


# Real Wage
# plot(Data_agr(Data,['Wf'],how='sum').values/Data_agr(Data,['Pf'],how='sum').values)

# Philips Curve
# plot((Nh-Data_agr(Data,['L'],how='sum')[12:])/Nh,Data_agr(Data,['Wf'],how='sum').pct_change(12)[12:],'.')


# Beveridge Curve
# plot(Data_agr(Data,['OP'],how='sum')/Nh,(Nh-Data_agr(Data,['L'],how='sum'))/Nh,'.')




#########################################################################

