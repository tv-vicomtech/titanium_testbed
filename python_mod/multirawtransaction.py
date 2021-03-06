#Lib for generate raw transaction, N to N 

from rpc_utils import *
from docker_utils import *
from btcconf import *
from zchconf import *
from oconf import *
from random import randint, random
from decimal import *
from datetime import datetime  
from datetime import timedelta  
import numpy
import random

txlist = []

def rand_list(nodelist,n_):
    answ=[]
    for idx in range(0,n_):
        r=randint(0,len(nodelist)-1)
        if(nodelist[r] not in answ):
            answ.append(nodelist[r])
        else:
            idx=idx-1
    return answ

def inicializar_txlist():
    txlist = []

def sum_all(send):
    s=0
    for idx in range(0,len(send)):
        s=s+send[idx]
    return s

def feeCorrect(send1,amountotal):
    tot=sum_all(send1)
    if (tot>=amountotal):
        return False
    else:
        return True

def transactions_nin_nout(client,destiny,origen,cryptotype,new):
    price_per_byte = 0.00000001
    getcontext().prec = 8    

    nvout=[]
    privkey=[]
    txid=[]
    amount=[]
    addr=[]
    pubKey=[]
    #print "......................................................"
    for out in destiny:
        if new is True:
            nn=rpc_call_newaddress(client,out,cryptotype)
            addr.append(nn)
            #print "TRUE --- "+str(addr)
        else:
            nn=rpc_call_accountaddress(client,out,cryptotype)
            addr.append(nn)
            #print "FALSE --- "+str(addr)
    #for out in addr:
    #    print out
    try:
        unspended = rpc_call_listunspent(client,origen,cryptotype)
        cont = len(unspended)
        #print "......................................................"
        #print "unspend= "+str(cont)
        amountotal = 0
        fee=0.003320
        if cont < 1:
            allin = False
        else:
            #if (cont<5):
            if (cont<3):
                n_inputs = randint(1,cont)
            else:
                n_inputs = randint(1,5)
            n_inputs=1
            n_outputs = len(destiny)

            #print "N {} input M {} output".format(n_inputs,n_outputs)

            allin = True

            fee = (n_inputs * 148 + n_outputs * 34 + 10) * price_per_byte
            fee=0.000332
            minfee=0.00001
            #print "......................................................"
            #print "fee= "+str(fee)
            amountotal=0
            c_iter=0
            while(c_iter<n_inputs):
                index = cont-1-c_iter
                txid.append(unspended[index]["txid"])   
                amount.append(unspended[index]["amount"])
                txaddr = unspended[index]["address"]
                pubKey.append(unspended[index]["scriptPubKey"])
                nvout.append(unspended[index]["vout"])
                dpk=rpc_call_dumpprivkey(client,origen,txaddr,cryptotype)
                privkey.append(dpk)
                amountotal=amountotal+unspended[index]["amount"]
                c_iter=c_iter+1

        if(amountotal>0.00001000):
            #print "amountotal ="+str(amountotal)
            #print "fee ="+str(fee)
            if(amountotal>Decimal(fee)):
                amountotal=amountotal-Decimal(fee)
            else:
                amountotal=amountotal-Decimal(minfee)
            #print "amountotal ="+str(amountotal)

            #print allin
            if allin is True: 
                checkfee=False
                num=0
                send1=[]
                while(not checkfee):
                    del send1[:]
                    amountotald = Decimal(amountotal)- Decimal(num*price_per_byte)
                    send=Decimal(amountotald/n_outputs)            
                    send1.append(round(send, 8))

                    for idx in range(1,n_outputs):
                        send=Decimal(amountotald/n_outputs)
                        send1.append(round(send, 8))
                    checkfee=feeCorrect(send1,amountotal)
                    num=num+1

                transin = '['
                for idx in range(0,n_inputs):
                    transin = transin+'{"txid":"' + txid[idx] + '","vout":'+str(nvout[idx])+'}'
                    if idx<(n_inputs-1):
                        transin=transin+','
                transin=transin+']'

                transout = '{"'
                for idx in range(0,n_outputs):
                    transout = transout+addr[idx]+'":'+str(send1[idx])
                    if idx<(n_outputs-1):
                        transout=transout+', "'
                transout=transout+'}'
                allowhighfees = True
                transtot = transin + "," + transout
                #print transtot
                rawtx=rpc_call_createrawtransaction(client,origen,transtot,cryptotype)

                if(rawtx!=False):
                    params = "'"+str(rawtx)+"'"
                    signrawtx=rpc_call_signrawtransaction(client,origen,params,cryptotype)
                    hextx = signrawtx["hex"]
                    allowhighfees = True
                    rawtrans = "'"+str(hextx)+"'"
                    rtxid=rpc_call_sendrawtransaction(client,origen,rawtrans,cryptotype)
    except:
        print("NO TX")

def create_raw_transaction(client,destiny,origen,amounttosend,new=True, inaddress=None, outaddress=None):
    nvout=[]
    privkey=[]
    txid=[]
    money=[]
    pubKey=[]
    allin = True
    cant = 0 
    data = False
    global txlist
    #balance = rpc_call(client,origen,'getbalance')
    addr = get_output_addresses(client,destiny,new,outaddress)
    inaddr=None
    tt=0
    for i in range(0,len(amounttosend)):
        tt=Decimal(amounttosend[i])+Decimal(tt)
    tt=round(tt, 8)
    if(inaddress is not None):
        inaddr =inaddress[0]
    input_num = 1

    for i in range(0,input_num):
        found = False
        original = tt
        #print "unspent" 
        data = search_input_in_unspent(client,origen,original,txid,nvout,privkey,money,inaddr)
        #print "unspent found "+str(data)
        #if (len(data)<3):
        #    print "mempool"
        #    data = search_input_in_mempool(client,origen,original,txid,nvout,privkey,inaddr)
    #print data
    if (len(data)<1):
        allin = False
    else:
        found = True            
    #print allin
    #print found
    if allin is True and found is True:
        for i in range(0,len(data),4):
            txid[i]= str(data[i][0]).encode("utf-8")
            nvout[i]=str(data[i][1])
            privkey[i]=str(data[i][2])
            money[i]=Decimal(data[i][3])

        input_num = len(txid)
        #change direction?
        ttmoney=0
        for i in range(0,len(money)):
            ttmoney=ttmoney+money[i]
        ttmoney=round(ttmoney, 8)

        fee=0.0003320
        rest=ttmoney-tt-fee
        #print "user money: "+str(ttmoney)
        #print "you want send: "+str(tt)
        if(rest<0):
            print("NO money")
            print("user money: "+str(ttmoney))
            print("you want send: "+str(tt))
            print("tx fee: "+str(fee))

        elif(rest>0):
            generate_raw_transaction(client,origen,destiny,txid,nvout,privkey,amounttosend,input_num,addr,rest)
        else:
            generate_raw_transaction(client,origen,destiny,txid,nvout,privkey,amounttosend,input_num,addr)

        time.sleep(15)

def get_output_addresses(client,destiny,new=True ,outaddress=None):
    addr = []
    out = len(destiny)
    if out > 0:
        for i in range(0,out):
            dest = str(destiny[i])
            #print dest + " "+str(new)
            if new is True:
                addr.append(rpc_call_newaddress(client,dest,"btc"))
                #print "TRUE --- "+str(addr)
            else:
                if outaddress is not None:
                    addr.append(outaddress[i])
                else:
                    addr.append(rpc_call_accountaddress(client,dest,"btc"))
                #print "FALSE --- "+str(addr)
        #for out in addr:
        #    print out
    return addr                   

def search_excatly_input_in_unspent(client,origen,original,txid,nvout,privkey,inaddress):
    found = False
    data = False
    global txlist
    cant = 0
    unspended = rpc_call(client, origen, 'listunspent')
    cont = len(unspended)
    if (cont > 0):
        for index in range(0,cont):
            if (inaddress is not None):
                in_addr = unspended[index]["address"]
                cant = unspended[index]["amount"]
                if (inaddr==inaddress and round(float(cant),8) == round(float(original),8)):
                    txaddr = unspended[index]["address"]
                    transid = unspended[index]["txid"]
                    txout = unspended[index]["vout"]
                    pkey = rpc_call(client, origen, 'dumpprivkey', '"' + str(txaddr) +'"')
                    txinlist = str(transid)+"_"+str(txout)
                   
                    if not (txinlist in txlist) and pkey!=False:
                        txid.append(transid)   
                        nvout.append(txout)
                        privkey.append(pkey)
                        found=True
                        txlist.append(txinlist)
                        data = {"found":found, "txid":txid, "nvout":nvout, "privkey":privkey}
                        break
            else:
                cant = unspended[index]["amount"]
                print(cant)
                print(original)
                if round(float(cant),8) == round(float(original),8):
                    txaddr = unspended[index]["address"]
                    transid = unspended[index]["txid"]
                    txout = unspended[index]["vout"]
                    pkey = rpc_call(client, origen, 'dumpprivkey', '"' + str(txaddr) +'"')
                    txinlist = str(transid)+"_"+str(txout)
                    
                    if not (txinlist in txlist) and pkey!=False:
                        txid.append(transid)   
                        nvout.append(txout)
                        privkey.append(pkey)
                        found=True
                        txlist.append(txinlist)
                        data = {"found":found, "txid":txid, "nvout":nvout, "privkey":privkey}
                        break
    return data

def search_input_in_unspent(client,origen,original,txid,nvout,privkey,money,inaddress):
    found = False
    data = []
    dataswap = []
    fee=0.0003320
    global txlist
    cant = 0
    unspended = rpc_call(client, origen, 'listunspent')
    cont = len(unspended)
    if (cont > 0):
        # for index in range(0,cont):
        #     if (inaddress is not None):
        #         in_addr = unspended[index]["address"]
        #         cant = unspended[index]["amount"]
        #         if (inaddr==inaddress and round(float(cant),8) == round(float(original),8)):
        #             txaddr = unspended[index]["address"]
        #             transid = unspended[index]["txid"]
        #             txout = unspended[index]["vout"]
        #             pkey = rpc_call(client, origen, 'dumpprivkey', '"' + str(txaddr) +'"')
        #             txinlist = str(transid)+"_"+str(txout)
                   
        #             if not (txinlist in txlist) and pkey!=False:
        #                 txid.append(transid)   
        #                 nvout.append(txout)
        #                 privkey.append(pkey)
        #                 money.append(cant)
        #                 found=True
        #                 txlist.append(txinlist)
        #                 data.append([transid,txout,pkey,cant])
        #                 break
        #     else:
        #         cant = unspended[index]["amount"]
        #         #print cant
        #         #print original
        #         if round(float(cant),8) == round(float(original),8):
        #             txaddr = unspended[index]["address"]
        #             transid = unspended[index]["txid"]
        #             txout = unspended[index]["vout"]
        #             pkey = rpc_call(client, origen, 'dumpprivkey', '"' + str(txaddr) +'"')
        #             txinlist = str(transid)+"_"+str(txout)
                    
        #             if not (txinlist in txlist) and pkey!=False:
        #                 txid.append(transid)   
        #                 nvout.append(txout)
        #                 privkey.append(pkey)
        #                 money.append(cant)
        #                 found=True
        #                 txlist.append(txinlist)
        #                 data.append([transid,txout,pkey,cant])

        #                 break
        # if (found is False):
        totalamount=0
        for index in range(0,cont):
            cant = unspended[index]["amount"]
            txaddr = unspended[index]["address"]
            transid = unspended[index]["txid"]
            txout = unspended[index]["vout"]
            pkey = rpc_call(client, origen, 'dumpprivkey', '"' + str(txaddr) +'"')
            txinlist = str(transid)+"_"+str(txout)
        
            if not (txinlist in txlist) and pkey!=False:
                txid.append(transid)   
                nvout.append(txout)
                privkey.append(pkey)
                money.append(cant)
                txlist.append(txinlist)
                totalamount=totalamount+cant
                dataswap.append([transid,txout,pkey,cant])

                if (totalamount>=original+fee):
                    found=True
                    data=dataswap
                    break
                        
    return data

def search_input_in_mempool(client,origen,original,txid,nvout,privkey,inaddress):
        found = False
        data = False
        global txlist
        cant = 0
        print(origen)
        mempool = rpc_call(client, origen,'getrawmempool')
        contm = len(mempool)
        print("mempool "+str(contm))
        if (contm > 0):
            for m in mempool:
                    txraw = rpc_call(client, origen, 'getrawtransaction', "'"+str(m)+"'")
                    unspendedmp = rpc_call(client, origen, 'decoderawtransaction', "'"+str(txraw)+"'")
                    outs = unspendedmp['vout']
                    
                    nouts = len(unspendedmp['vout'])
                    for n in range(0, nouts):
                        if (inaddress is not None):
                            in_addr = outs[n]["scriptPubKey"]["addresses"][0]
                            cant = outs[n]["value"]

                            if (in_addr==inaddress and round(float(original),8)==round(float(cant),8)):
                                txout = outs[n]["n"]
                                txaddr = outs[n]["scriptPubKey"]["addresses"][0]
                                pkey = rpc_call(client, origen, 'dumpprivkey', '"' + str(txaddr) +'"')
                                txinlist = str(m)+"_"+str(txout)
                                
                                if not (txinlist in txlist) and pkey!=False:
                                    privkey.append(pkey)
                                    txid.append(str(m))
                                    nvout.append(txout)
                                    found=True
                                    txlist.append(txinlist)
                                    data = {"found":found, "txid":txid, "nvout":nvout, "privkey":privkey}
                                    break 
                        else:      
                            cant = outs[n]["value"]
                            if (round(float(original),8)==round(float(cant),8)):
                                txout = outs[n]["n"]
                                txaddr = outs[n]["scriptPubKey"]["addresses"][0]
                                pkey = rpc_call(client, origen, 'dumpprivkey', '"' + str(txaddr) +'"')
                                txinlist = str(m)+"_"+str(txout)
                                
                                if not (txinlist in txlist) and pkey!=False:
                                    privkey.append(pkey)
                                    txid.append(str(m))
                                    nvout.append(txout)
                                    found=True
                                    txlist.append(txinlist)
                                    data = {"found":found, "txid":txid, "nvout":nvout, "privkey":privkey}#, "cant":cant}
                                    break      
                    if (found is True):
                        break
        return data

def generate_raw_transaction(client,origen,destiny,txid,nvout,privkey,amounttosend,input_num,outaddress,rest=None):
        addr = outaddress
        n_inputs = input_num
        n_outputs = len(destiny)

        # for a in destiny:
        #     #addr.append(rpc_call(client, a, 'getaccountaddress', '""'))
        #     addr.append(rpc_call(client, a, 'getnewaddress'))
        #for idx in range(0,n_inputs):
            #print'{"txid":"' + str(txid[idx]) + '","vout":'+str(nvout[idx])+'}'
        transin = '['
        for idx in range(0,n_inputs):
            transin = transin+'{"txid":"' + str(txid[idx]) + '","vout":'+str(nvout[idx])+'}'
            if idx<(n_inputs-1):
                transin=transin+','
        transin=transin+']'

        transout = '{"'
        for idx in range(0,n_outputs):
            #print str(amounttosend[idx])
            transout = transout+addr[idx]+'":'+str(amounttosend[idx])
            if idx<(n_outputs-1):
                transout=transout+', "'

        #change direction
        if(rest is not None):
            change_address = rpc_call(client,str(origen),'getnewaddress','""')
            transout = transout+',"'+change_address+'":'+str(rest)

        transout=transout+'}'
        allowhighfees = True
        transtot = transin + "," + transout + ","+str(0)+","+str(allowhighfees)
        #print transtot
        rawtx = rpc_call(client, origen, 'createrawtransaction', transtot)
        if(rawtx!=False):
            dectx = rpc_call(client, origen, 'decoderawtransaction', '"' + rawtx + '"')

            privkeys = '["'
            for idx in range(0,len(privkey)):
                privkeys = privkeys+privkey[idx]
                if idx<(len(privkey)-1):
                    privkeys=privkeys+'","'
            privkeys=privkeys+'"]'

            output = []
            transprivkeys = '"'+str(rawtx)+'",'+str(output)+','+str(privkeys)+',"ALL"'

            signrawtx = rpc_call(client, origen, 'signrawtransaction', transprivkeys )
            #print signrawtx
            #print transprivkeys
            #print "*******    ********"
            if(signrawtx!=False):
                hextx = signrawtx["hex"]
                allowhighfees = True
                rawtrans = '"'+str(hextx)+'",'+str(allowhighfees)
                #print rawtrans
                rtxid = rpc_call(client, origen, 'sendrawtransaction', str(rawtrans))

def send_to_address_anc_check_balance (client,source,amount,destination,cryptotype="btc",newval=False):
    info=[]
    amount_verify=float(amount)
    if newval is False:
        if(cryptotype=="btc"):
            validation= rpc_call(client, source, 'validateaddress','"'+destination+'"')
        elif(cryptotype=="zch"):
            validation= rpc_call(client, source, 'validateaddress','"'+destination+'"',ZCH_RPC_USER,ZCH_RPC_PASSWD, ZCH_RPC_PORT)
    else:
        validation = {}
        validation['isvalid']=True
        if(cryptotype=="btc"):
            destination=rpc_call(client, destination, 'getnewaddress','""')
        elif(cryptotype=="zch"):
            destination=rpc_call(client, destination, 'getnewaddress','""',ZCH_RPC_USER,ZCH_RPC_PASSWD, ZCH_RPC_PORT)

    if(validation['isvalid']):
        if(cryptotype=="btc"):
            balance= rpc_call(client, source, 'getbalance')
        elif(cryptotype=="zch"):
            balance= rpc_call(client, source, 'getbalance',"",ZCH_RPC_USER,ZCH_RPC_PASSWD, ZCH_RPC_PORT)
        if(balance>=amount_verify):
            if(cryptotype=="btc"):
                tx=rpc_call(client, source, 'sendtoaddress',"'"+destination+"','"+str(amount)+"'")
            elif(cryptotype=="zch"):
                tx=rpc_call(client, source, 'sendtoaddress',"'"+destination+"','"+str(amount)+"'",ZCH_RPC_USER,ZCH_RPC_PASSWD, ZCH_RPC_PORT)
            print(tx)
            info.append(source+" send to "+destination+" "+str(amount)+" "+cryptotype)
            info.append("Transaction done!")
            return info

        else:
            info.append("Wallet not have enough funds!")
            return info
    else:
        info.append("Destination address not valid!")
        return info

def send_to_address (client,source,amount,destination,cryptotype="btc",newval=False):
    info=[]
    amount_verify=float(amount)
    if newval is False:
        if(cryptotype=="btc"):
            validation= rpc_call(client, source, 'validateaddress','"'+destination+'"')
        elif(cryptotype=="zch"):
            validation= rpc_call(client, source, 'validateaddress','"'+destination+'"',ZCH_RPC_USER,ZCH_RPC_PASSWD, ZCH_RPC_PORT)
    else:
        validation = {}
        validation['isvalid']=True
        if(cryptotype=="btc"):
            destination=rpc_call(client, destination, 'getnewaddress','""')
        elif(cryptotype=="zch"):
            destination=rpc_call(client, destination, 'getnewaddress','""',ZCH_RPC_USER,ZCH_RPC_PASSWD, ZCH_RPC_PORT)

    if(validation['isvalid']):
        if(cryptotype=="btc"):
            tx=rpc_call(client, source, 'sendtoaddress',"'"+destination+"','"+str(amount)+"'")
        elif(cryptotype=="zch"):
            tx=rpc_call(client, source, 'sendtoaddress',"'"+destination+"','"+str(amount)+"'",ZCH_RPC_USER,ZCH_RPC_PASSWD, ZCH_RPC_PORT)
        print(tx)
        info.append(source+" send to "+destination+" "+str(amount)+" "+cryptotype)
        info.append("Transaction done!")
        return info
    else:
        info.append("Destination address not valid!")
        return info

def generaterandomtransaction(client,nodelist,cryptotype,howmanyblock):
    info=[]
    txnum=0
    totalblock=0
    totalblock=rpc_call_blockcount(client,nodelist[0],cryptotype)
    blcknum=0
    miningNumber=randint(20,40)
    while(blcknum<howmanyblock):
        print("transaction:"+str(txnum))
        origen=[]
        destiny=[]
      
        r= randint(1, 10)
        if r < 7:
            s = randint(0,len(nodelist)-1)
            source = nodelist[s]
            try:
                amount = rpc_call_balance(client,source,cryptotype)
            except:
                print("NO TX")
                amount = 0
            d = randint(0,len(nodelist)-1)
            while(s==d):
                d = randint(0,len(nodelist)-1)

            if r < 5:
                dest=rpc_call_newaddress(client,nodelist[d],cryptotype)
                
                if(amount>0.0000100):
                    ran=random.random()*float(amount)
                    amount_random=round(ran, 8)
                else:
                    amount_random=amount

                if(amount_random>0.0000100):
                    rpc_call_sendmondey(client,source,dest,str(amount_random),cryptotype)
                    txnum +=1
                else:
                    print("***this wallet("+nodelist[d]+") is skipped!")
            else:
                #print "Using a change address"
                destiny.append(str(nodelist[d]))
                transactions_nin_nout(client,destiny,source,cryptotype,True)
                txnum +=1
        else:
            n_in = randint(0,len(nodelist)-1)
            n_out = randint(2,10) # max number of destiny
            origen = nodelist[n_in]
            destiny = rand_list(nodelist,n_out)
            transactions_nin_nout(client,destiny,origen,cryptotype,True)
            txnum +=1
        time.sleep(2)
        if(txnum==miningNumber):
            print("******Mining a new block*****")
            time.sleep(2)
            idx = randint(0,len(nodelist)-1)
            rpc_call_generate(client,nodelist[idx],"1",cryptotype)
            
            blcknum +=1

            info.append("CREATED block Number: "+str(int(totalblock)+blcknum))
            info.append("* with tx: "+str(txnum))

            print("Block height: " + str(int(totalblock)+blcknum))
            print("Number of transactions: "+str(txnum))
            txnum=0
            miningNumber=randint(40,150)
            time.sleep(2)

    print("*****OK*****")
    return info

def test_transaction(client,nodelist):
    for idx in range(0,1):
        print("transaction:"+str(idx))
        s = idx
        source = nodelist[s].name
        destiny=[]
        amounttosend=[]
        d = (len(nodelist)-idx-1)
        destiny.append(str(nodelist[d].name))
        destiny.append(str(nodelist[d-1].name))
        destiny.append(str(nodelist[d-2].name))
        amounttosend.append(0.125)
        amounttosend.append(0.125)
        amounttosend.append(0.125)
        create_raw_transaction(client,destiny,source,amounttosend)
       
    rpc_call(client, nodelist[1].name, 'generate', '1')



def generatefixtransaction(client,nodelist):
    # generate 50 new block with 20 transactions of sendtoaddress, 15 change transactions, and 15 RAW transactions
    # with fix nodes sender (the first 50 blocks that we know have money) and receiver 
    txnum=0
    blcknum=0

    for gen in range(0,50):
        origen=[]
        destiny=[]

        for idx in range(0,19):
            print("transaction:"+str(txnum))
            s = idx
            source = nodelist[s].name
            amount= rpc_call(client, source, 'getbalance')
            print(source+" have:"+str(amount))
            d = (len(nodelist)-idx-1)
            dest=rpc_call(client, nodelist[d].name, 'getnewaddress')
            if(amount>0.125):
                ran=0.125
                amount_random=round(ran, 8)
            else:
                amount_random=amount

            if(amount_random>0.00000001):
                #print "Generating transactions: " + str(amount_random) + " BTCs"
                rpc_call(client, source, 'sendtoaddress', "'" +dest+ "','" + str(amount_random) + "'")
                txnum +=1
        for idx in range(20,35):
            print("transaction:"+str(txnum))
            s = idx
            source = nodelist[s].name
            destiny=[]
            amounttosend=[]
            d = (len(nodelist)-idx-1)
            destiny.append(str(nodelist[d].name))
            amounttosend.append(0.125)
            create_raw_transaction(client,destiny,source,amounttosend)
            txnum +=1
        for idx in range(36,50):
            print("transaction:"+str(txnum))
            s = idx
            source = nodelist[s].name
            destiny=[]
            amounttosend=[]
            d = (len(nodelist)-idx-1)
            destiny.append(str(nodelist[d].name))
            destiny.append(str(nodelist[d-1].name))
            destiny.append(str(nodelist[d-2].name))
            amounttosend.append(0.125)
            amounttosend.append(0.125)
            amounttosend.append(0.125)
            create_raw_transaction(client,destiny,source,amounttosend)
            txnum +=1

        print("******Mining a new block*****")
        time.sleep(2)
        rpc_call(client, nodelist[0].name, 'generate', '1')
        numblock = rpc_call(client, nodelist[idx].name, 'getblockcount')
        blcknum +=1
        print("Block height: " + str(numblock))
        print("Number of transactions: "+str(txnum))
        time.sleep(2)

    print("*****OK*****")

def generatetransactionset(client,nodelist):
    txnum = 0
    numblocks = 0
    #for i in range(1,6):
    for i in range(1,2):
        origen=[]
        destiny=[]
        cont = 0
        nodeind = 0
        c = 1
        for j in range(0,len(nodelist)):
            node = nodelist[j].name
            if (j == len(nodelist)-1):
                nodedest = nodelist[0].name
            else:
                nodedest = nodelist[j+1].name
            dest = rpc_call(client,nodedest,'getnewaddress')
            if (rpc_call(client,node,'getbalance')>c):
                print("Generating transactions: " + str(c) + " BTCs")
                rpc_call(client, nodelist[j].name, 'sendtoaddress', "'" +dest+ "','" + str(c) + "'")
                txnum +=1
                cont +=1
            time.sleep(2)
            if (cont == 5):
                print("******Mining a new block*****")
                time.sleep(2)
                rpc_call(client, nodelist[nodeind].name, 'generate', '1')
                numblock = rpc_call(client, nodelist[nodeind].name, 'getblockcount')
                txnum +=1
                numblocks +=1
                if (nodeind < len(nodelist)):
                    nodeind +=1
                else:
                    nodeind = 0
                cont = 0
                print("Block height: " + str(numblock))
                print("Number of transactions: "+str(txnum))
                #time.sleep(2)
        print("Using a change address")
        for j in range(0,len(nodelist)):
            destiny = []
            origen = str(nodelist[j].name)
            if (j == len(nodelist)-1):
                destiny.append(str(nodelist[0].name))
            else:
                destiny.append(str(nodelist[j+1].name))
            destiny.append(str(nodelist[j].name))
            transactions_nin_nout(client,destiny,origen,"btc",True)
            txnum +=1
            cont +=1
            time.sleep(2)
            if (cont == 5):
                print("******Mining a new block*****")
                time.sleep(2)
                rpc_call(client, nodelist[nodeind].name, 'generate', '1')
                numblock = rpc_call(client, nodelist[nodeind].name, 'getblockcount')
                txnum +=1
                numblocks +=1
                if (nodeind < len(nodelist)):
                    nodeind +=1
                else:
                    nodeind = 0
                cont = 0
                print("Block height: " + str(numblock))
                print("Number of transactions: "+str(txnum))
                #time.sleep(2)
        for j in range(0,len(nodelist)):
            print("N inputs M outputs")
            origen = nodelist[j].name
            destiny = []
            if (j < len(nodelist)-3):
                destiny.append(nodelist[j+1].name)
                destiny.append(nodelist[j+2].name)
                destiny.append(nodelist[j+3].name)
            elif (j == len(nodelist)-3):
                destiny.append(nodelist[j+1].name)
                destiny.append(nodelist[j+2].name)
                destiny.append(nodelist[0].name)
            elif (j == len(nodelist)-2):
                destiny.append(nodelist[j+1].name)
                destiny.append(nodelist[0].name)
                destiny.append(nodelist[1].name)
            elif (j == len(nodelist)-1):
                destiny.append(nodelist[0].name)
                destiny.append(nodelist[1].name)
                destiny.append(nodelist[2].name)
            transactions_nin_nout(client,destiny,origen,"btc",True)
            txnum +=1
            cont +=1
            time.sleep(2)
            if (cont == 5):
                print("******Mining a new block*****")
                time.sleep(2)
                rpc_call(client, nodelist[0].name, 'generate', '1')
                numblock = rpc_call(client, nodelist[0].name, 'getblockcount')
                txnum +=1
      
                cont = 0
                print("Block height: " + str(numblock))
                print("Number of transactions: "+str(txnum))
                #time.sleep(2)
        time.sleep(10)
        rpc_call(client, nodelist[0].name, 'generate', '1')
        numblock = rpc_call(client, nodelist[0].name, 'getblockcount')
        txnum +=1
        print("Block height: " + str(numblock))
        print("Number of transactions: "+ str(txnum))
        print("*****OK*****")


def mining_blocks(client,source,cryptotype,num_to_gen):
    print("MINING BLOCK "+cryptotype)
    numberblock = str(num_to_gen)
    msg=[]
    if(cryptotype=="btc") :
        try:
            rpc_call(client, source, 'generate', numberblock)
        except:
            return "no block mined"
    elif(cryptotype=="zch"):
        try:
            rpc_call(client, source, 'generate', numberblock,ZCH_RPC_USER, ZCH_RPC_PASSWD, ZCH_RPC_PORT)
        except:
            return "no block mined"
    time.sleep(3)

    msg.append(numberblock+" blocks are generated")

    print("********************")
    print(str(numberblock)+" blocks are generated")
    return msg

def send_money_to_all(client,source,nodelist,cryptotype="btc"):
    print("GENERATE transaction "+cryptotype)
    info=[]
    time.sleep(1)
    #print cryptotype
    if(cryptotype=="btc"):
        balance=rpc_call(client, source, 'getbalance',"")
    elif(cryptotype=="zch"):
        balance=rpc_call(client, source, 'getbalance', "",ZCH_RPC_USER, ZCH_RPC_PASSWD, ZCH_RPC_PORT)
    amount=balance/10
    if(balance>0.0001):
        for i in range(0,len(nodelist)):
            if(cryptotype=="btc"):
                balance=rpc_call(client, source, 'getbalance',"")
            elif(cryptotype=="zch"):
                balance=rpc_call(client, source, 'getbalance', "",ZCH_RPC_USER, ZCH_RPC_PASSWD, ZCH_RPC_PORT)
            if(balance>=amount):
                amount=round(amount,8)
                if(amount<0.00001):
                    amount=0.00001
                if(cryptotype=="btc") :
                    dest=rpc_call(client, nodelist[i], 'getnewaddress', "")
                    rpc_call(client, source , 'sendtoaddress', "'" +dest+ "','" + str(amount) + "'")
                    print(source +" send "+ str(amount) +" "+cryptotype+" to "+ dest+ "("+nodelist[i]+")")
                elif(cryptotype=="zch"):
                    dest=rpc_call(client, nodelist[i], 'getnewaddress', "",ZCH_RPC_USER, ZCH_RPC_PASSWD, ZCH_RPC_PORT)
                    rpc_call(client, source , 'sendtoaddress', "'" +dest+ "','" + str(amount) + "'",ZCH_RPC_USER, ZCH_RPC_PASSWD, ZCH_RPC_PORT)
            else:
            	print("amount:" +str(amount)+" balance:"+str(balance))

        if(cryptotype=="btc") :
            time.sleep(10)
            rpc_call(client, source, 'generate', '1')
        elif(cryptotype=="zch"):
            rpc_call(client, source , 'generate','1' ,ZCH_RPC_USER, ZCH_RPC_PASSWD, ZCH_RPC_PORT)
        print("ALL WALLET ARE FULL")
        info.append("Wallets filled")

    else:
        info.append("Don't have enough funds to send")
        print("Don't have enough funds to send")

    time.sleep(1)

    print("********************")

    return info


