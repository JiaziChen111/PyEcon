# -*- coding: utf-8 -*-
import os
from scipy import *
import scipy.optimize as opt
import pandas as pd
import datetime




# /// INPUTS /// 
# 年齢
Age_0 = 33 # 現在年齢（才）
Age_r = 50 # 残存余命（年）
Age_ret = 60 # 退職金受取年齢
Age_str = 24 # 就職開始年齢


# 家族
Age_m = 28 # 結婚時の本人年齢（予定なしの場合は0）
Age_d = 3 # 配偶者との年齢差（本人－配偶者）

N_c = 2 # 子どもの数（含む予定）
Age_c = [35, 37] # 出生時の本人年齢（才）

psh = [[0,0,0,0], # 1st 小中高大
       [0,0,0,0]] # 2nd　小中高大


# 世帯支出
C_c0 = 30 # コア月間消費
D_n0 = 0 # 住宅以外ローン（多目的、無担保）現在高


# 住宅
F_h0 = 15000 # 住宅（保有or購入対象）・現在評価額（万円）
Age_h = 37 #住宅購入時の本人年齢
D_h0 = 0 # 住宅ローン現在高
Rent_h = 43 # 居住用家賃（月間、万円）


# 資産運用
s_r = 0.2 # 新規貯蓄の預金・リスク資産配分

A_d0 = 300 # 現在の預金残高（万円）
A_r0 = 150 # 現在のリスク資産残高（万円）




#　遺産
Inh_T = 1000 # 目標純遺産額の現在額（万円）


# 収入 
# 年収カーブを入力（本人と配偶者）
stc = 20
edc = 100
W_m0 = 1800
W_s0 = 300



# /// Parameters ///
pi_w = 0.0 #マクロ賃金上昇率（年率）
pi_p = 0.0 #物価インフレ率
pi_h = 0.0 #家賃インフレ率（年率）
pi_r = 0.0 #実質リスク資産価格伸び率

i_d = 0.0   #預金利子率（年率）
i_r = 0.015 #リスク資産（配当・分配金）利回り
i_h = 0.01 #住宅ローン利子率（年率）
i_n = 0.06 #無担保ローン利子率（年率）
i_f = 0.0 #リスクフリー金利

h_dur = 35 #住宅ローン年限（年）
h_pre = 0.1 #住宅ローン頭金割合
h_dep = 50 #住宅耐用年数（年）
n_dur = 10 #無担保ローン年限（年）
n_lim = 0.3 # 無担保ローン年収制限

s_c = [0.1, 0.1] # 企業年金の年間拠出額／年収比率（本人, 配偶者）
A_cd0 = [200, 50] # 企業年金・元本保証の現在残高（万円）（本人, 配偶者）
A_cr0 = [100, 50] # 企業年金・リスク資産の現在残高（万円）（本人, 配偶者）


cld = [93,88,94,104,120,116,122,111,110,113,115,124,127,153,153,161,161,161,161,200,200,200,200] #子供の年齢－費用カーブ（全て公立）
psh_add = array(psh)*array([112, 85, 58, 55]) #私立追加支出


t_r = 0.2 #　証券税率



# /// Tax Functions /// 

def DW(W,W_s,cages,Life=0): 
    """
    手取り所得計算（所得税、社会保険料）
    """
    # 社会保険料
    S = 0.1*W 
    
    #　基礎控除
    D_0 = 38 
    
    # 給与所得控除
    if W<65.:
        D_w = 65.
    elif 65<= W <180:
        D_w = W*0.4
    elif 180<= W <360:
        D_w = W*0.3 + 18
    elif 360<= W <660:
        D_w = W*0.2 +54
    elif 660<= W <1000:
        D_w = W*0.1 +120
    elif 1000<=W:
        D_w = 220
    
    #　配偶者控除
    if W_s<105:
        D_s = 38
    elif 105<=W_s<110:
        D_s = 36
    elif 110<=W_s<115:
        D_s = 31
    elif 115<=W_s<120:
        D_s = 26
    elif 120<=W_s<125:
        D_s = 21
    elif 125<=W_s<130:
        D_s = 16
    elif 130<=W_s<135:
        D_s = 11
    elif 135<=W_s<140:
        D_s = 6
    elif 140<=W_s<141:
        D_s = 3
    elif 141<=W_s:
        D_s = 0
    
    
    # 扶養控除
    Cages = cages[cages>=0]
    D_c = 0
    for cage in Cages:
        if cage <19:
            D_c += 38
        elif 19<=cage<23:
            D_c += 63
            
    # 生命保険料控除
    if Life <=2:
        D_l = Life
    elif 2<Life<=4:
        D_l = Life*0.5 + 1
    elif 4<Life<=8:
        D_l = Life*0.25 + 2    
    elif 8<=Life:
        D_l = 4
    
    
    # 課税所得額
    TW = W - S - D_0 - D_w - D_s - D_l
    
    #　所得税率
    if TW<195:
        Tax = TW*0.05
    elif 195<=TW<330:
        Tax = TW*0.1 - 9.75
    elif 330<=TW<695:
        Tax = TW*0.2 - 42.75
    elif 695<=TW<900:
        Tax = TW*0.23 - 63.6
    elif 900<=TW<1800:
        Tax = TW*0.33 - 153.6
    elif 1800<=TW<4000:
        Tax = TW*0.40 - 279.6
    elif 4000<=TW:
        Tax = TW*0.45 - 479.6
    
    # 住民税
    TaxR = TW*0.1
    
    #　可処分所得
    DW = W-S-Tax-TaxR
    
    return DW


#　退職金所得税
def Dret(ret,wyears):
    if wyears<=20:
        D = 40*wyears
    elif 20<wyears:
        D = 800 + 70*(wyears - 20)
    
    Tret = (ret - D)*0.5
    
    # 退職所得税
    if Tret<195:
        Tax = Tret*0.05
    elif 195<=Tret<330:
        Tax = Tret*0.1 - 9.75    
    elif 330<=Tret<695:
        Tax = Tret*0.2 - 42.75    
    elif 695<=Tret<900:
        Tax = Tret*0.23 - 63.6    
    elif 900<=Tret<1800:
        Tax = Tret*0.33 - 153.6
    elif 1800<=Tret<4000:
        Tax = Tret*0.4 - 279.6
    elif 4000<=Tret:
        Tax = Tret*0.45 - 479.6
        
    #　住民税
    TaxR = Tret*0.1
    
    Dret = ret - Tax - TaxR
    return Dret


# 固定資産税
def TaxF(F_h):
    return (F_h*0.65)*0.014




# 住宅ローン減税
def RTaxD_h(D_h,t,Age,Age_h):
    Age_h_lim = Age_h + 10
    Redu = min(D_h, 4000)*0.01 if t.year <=2018 and Age <=Age_h_lim else 0
    return Redu






# /// Model /// -------------------------------------------
class Model(pd.DataFrame):
    def __init__(self,*args, **kwords):
        super(Model, self).__init__(
        *args, **kwords)

        
    def variable(self, varname, init=0):
        self[varname]=repeat(nan,self.shape[0])
        self[varname][0] = init
        
        
    def run(self,**pars):

        # value setting from external pars         
        for par in pars:
            src = par+"="+str(pars[par])
            exec(src)
        
        
        # /// Variable initialize ///
        W_m = ones(edc-stc); W_m[:Age_ret-stc]=W_m0; W_m[Age_ret-stc:]=sum(W_m[:Age_ret-stc])/200+75
        W_s = ones(edc-stc); W_s[:Age_ret-stc]=W_s0; W_s[Age_ret-stc:]=sum(W_s[:Age_ret-stc])/200+75
        
        self.variable('Y_wm', init = W_m[Age_0-stc]) #本人給与
        self.variable('Y_dwm') #本人手取り給与
        self.variable('Y_ws', init = W_s[Age_0-Age_d-stc]) #配偶者給与
        self.variable('Y_dws') #配偶者手取り給与
        self.variable('Y') #可処分所得
        self.variable('Y_w') #勤労手取り所得
        self.variable('Y_ii') #インカムゲイン
        self.variable('Y_ic') #キャピタルゲイン
        self.variable('RTaxD_h') # 住宅ローン減税還付金
        
        self.variable('F_h') #住宅資産
        
        self.variable('A_d', init = A_d0) #現預金
        self.variable('A_r', init = A_r0) #リスク資産
        self.variable('A_cmd', init = A_cd0[0]) #企業年金・本人・元本保証
        self.variable('A_cmr', init = A_cr0[0]) #企業年金・本人・リスク資産
        self.variable('A_csd', init = A_cd0[1]) #企業年金・配偶者・元本保証
        self.variable('A_csr', init = A_cr0[1]) #企業年金・配偶者・リスク資産
        
        self.variable('C_c', init = C_c0*12) #コア消費
        self.variable('C') #消費
        
        self.variable('D_h', init = D_h0) #住宅ローン
        self.variable('D_n', init = D_n0) #無担保ローン
        
        self.variable('C_cld') #子ども支出
        self.variable('C_c') #コア消費支出
        self.variable('C_rnt') #家賃
        self.variable('C_hi') #住宅利払い
        self.variable('C_hp') #住宅元本払い
        self.variable('C_ni') #無担保利払い
        self.variable('C_np') #無担保元本払い
        
        self.variable('TaxF') #固定資産税
                
        new_hdebt = 0; new_ndebt = 0

        
        # /// Time transition ///
        for i, t in enumerate(self.index[1:],1):
        
        #i=1;t=self.index[1]
        
            # Ages 
            Age = i+Age_0
            cages = array(Age_c)-Age
            
            
            # Working or pension Income
            self['Y_wm'][t] = (1.+ pi_w + (W_m[i]/W_m[i-1]-1.))*self['Y_wm'][t-1]            
            self['Y_ws'][t] = (1.+ pi_w + (W_s[i]/W_s[i-1]-1.))*self['Y_ws'][t-1]
 
            # Disposable working income
            self['Y_dwm'][t]= DW(self['Y_wm'][t],self['Y_ws'][t],cages)
            self['Y_dws'][t]= DW(self['Y_ws'][t],self['Y_wm'][t], cages)
            
        
            # Total employment compensation
            self['Y_w'][t] = self.Y_dwm[t] + self.Y_dws[t]
            
            # Asset Income
            self['Y_ii'][t] = (i_d*self['A_d'][t-1] + i_r*self['A_r'][t-1])*(1.-t_r)
            self['Y_ic'][t]= ((pi_p + pi_r)*self['A_r'][t-1])*(1.-t_r)
            self['Y_i'] = self.Y_ii + self.Y_ic
        
            
            # Retirement allowance
            ret_m = Dret(self[['A_cmd','A_cmr']].sum(1)[t-1],Age_ret-Age_str) if Age == Age_ret else 0.0
            ret_s = Dret(self[['A_csd','A_csr']].sum(1)[t-1],Age_ret-Age_str) if Age-Age_d == Age_ret else 0.0        

            #　Tax reduction on housing debt
            self['RTaxD_h'][t] = RTaxD_h(self.D_h[t-1],t,Age,Age_h)
            
            # Total disposable Income
            self['Y'][t] = self.Y_w[t] + self.Y_i[t] + ret_m + ret_s  + self.RTaxD_h[t]
            
            # Core Consumption
            self['C_c'][t] = C_c0*12*power(1.+pi_p,i)
            
            
            # Child care
            cldcost = 0
            for c,add in zip(Age_c,psh_add):
                cage = Age - c
                if 6< cage <=12:
                    add_cld = add[0]
                elif 12 < cage <=15:
                    add_cld = add[1]
                elif 15 < cage <=18:
                    add_cld = add[2]        
                elif 18 < cage <=22:
                    add_cld = add[3]
                else:
                    add_cld = 0.
                
                if 0 <= cage < len(cld):
                    cldcost += cld[cage] + add_cld
                    
            self['C_cld'][t] = cldcost*power(1.+pi_p,i)
            
            
            # Rent payment
            self['C_rnt'][t] = 0 if Age > Age_h else power(1.+pi_h,i)*Rent_h
            
            # Debt cost payment
            new_hvalue = power(1.0+pi_h,i)*F_h0
            new_hdebt = new_hvalue*(1.-h_pre)  if Age == Age_h else 0.
            h_precost = new_hvalue*h_pre  if Age == Age_h else 0.
            
            self['C_hi'][t] = i_h * self.D_h[t-1]
            self['C_hp'][t] = new_hdebt/h_dur + self['C_hp'][t-1] if self['D_h'][t-1]>=self['C_hp'][t-1] else self['D_h'][t-1]
            
            self['C_ni'][t] = i_n * self.D_n[t-1]
            self['C_np'][t] = new_ndebt/n_dur + self['C_np'][t-1] if self['D_n'][t-1]>=self['C_np'][t-1] else self['D_n'][t-1]
            
            self['C_d'] = self.C_hi + self.C_hp + self.C_ni + self.C_np
            
            #　Fixed asset tax
            self['TaxF'][t] = TaxF(self.F_h[t-1])
            
            # Total expenditure
            self['C'][t] = self.C_c[t] + self.C_cld[t] + self.C_d[t] + self.TaxF[t] + h_precost
            
            
            # Household balance (saving or borrowing)
            self['NET'] = self.Y - self.C
            surplus = max(self.NET[t],0.)
            deficit = min(self.NET[t],0.)
            
            # New uncollateralized loan
            new_ndebt = 0. if self.A_d[t-1]+self.A_r[t-1] + deficit >= 0.0 else -(self.A_d[t-1]+self.A_r[t-1] + deficit)
            
            new_nlim = n_lim*self.Y_w[t-1] - self.D_n[t-1]
            new_ndebt = min(new_ndebt, new_nlim)
            
            
            # Fixed housing asset
            self['F_h'][t] = self['F_h'][t-1] + new_hvalue if Age == Age_h else self['F_h'][t-1]*max(1.-(1./h_dep)*max(Age-Age_h,0),0)*power(1.+pi_h,i)
            
            
            # Financial asset
            self['A_d'][t] = self['A_d'][t-1] + (surplus+deficit+ new_ndebt)*(1.-s_r)  
            self['A_r'][t] = self['A_r'][t-1] + (surplus+deficit+ new_ndebt)*s_r 
            
            
            # Debt
            self['D_h'][t] = self['D_h'][t-1] - self['C_hp'][t] + new_hdebt
            self['D_n'][t] = self['D_n'][t-1] - self['C_np'][t] + new_ndebt
            
            
            # Corporate pention plan
            if Age<Age_ret:
                self['A_cmd'][t] = (1.+i_d)*self['A_cmd'][t-1] + self['Y_wm'][t]*s_c[0]*(1.-s_r)
                self['A_cmr'][t] = (1.+i_r)*self['A_cmr'][t-1] + self['Y_wm'][t]*s_c[0]*(s_r)
            else:
                self['A_cmd'][t]=0; self['A_cmr'][t]=0
                
            
            if Age-Age_d<Age_ret:
                self['A_csd'][t] = (1.+i_d)*self['A_csd'][t-1] + self['Y_ws'][t]*s_c[1]*(1.-s_r)
                self['A_csr'][t] = (1.+i_r)*self['A_csr'][t-1] + self['Y_ws'][t]*s_c[1]*(s_r)
            else:
                self['A_csd'][t]=0; self['A_csr'][t]=0
            
            self['A_c'] = self.A_cmd + self.A_cmr + self.A_csd + self.A_csr 
        
        # Aggregates
        self['A_f'] = self.A_d + self.A_r
        self['A'] = self.A_f + self.A_c + self.F_h
        self['D'] = self.D_h + self.D_n
        self['NW'] = self.A - self.D
        



# /// Prep ///
thisy = datetime.datetime.today().year
lasty = thisy-1
endy = thisy + Age_r
ind = pd.period_range(start=lasty, end=endy, freq="A")

MOD = Model(index=ind)









# /// Optimization ///
#def obj(par_val, parname='C_c0', MOD=MOD):   
#    MOD.run(**{parname:par_val})
#    Rf = array([power(1.+i_f,t) for t in range(MOD.shape[0])])
#    
#    # Present value of net worth
#    NW_CV = dot(MOD.NET,1./Rf) + MOD.NW[0] - MOD.A_c[0]
#    
#    # Constraint
#    pnlt = (-10**10)*MOD.A_f[MOD.A_f<0].sum()
#    
#    return abs(NW_CV - Inh_T) + pnlt
#    
#    
#    
#x_star = opt.fminbound(obj,500,1500)
#
#
#MOD.run(**{'C_c0':x_star})











"""
/// Future development ///

・　現実的な賃金カーブ
・　投資用住宅購入
・　貯蓄型生命保険
・　2世帯生活（勤労親、勤労子との同居）の可能性

"""



