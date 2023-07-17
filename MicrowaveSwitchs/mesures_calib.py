import numpy as np
import matplotlib.pyplot as plt
import os

def all_open(force = False):
    dev.command_every_port("open", 61, force=force)
    dev.command_every_port("open", 60, force=force)

def all_close(force = False):
    dev.command_every_port("close", 61, force=force)
    dev.command_every_port("close", 60, force=force)
            
    
def plot_S(time):
    fname = ''
    print 'Pas encore implemente'
    L = os.listdir(os.getcwd())
    for filename in L:
        print filename[-10:-4]
        if filename[-10:-4] == str(time):
            fname = filename
            print 'him u found me \n fname = '
            print fname
            break
    print fname
    with open(fname) as f:
        contents = f.readlines()
        freq, S11, S12, S21, S22 = [], [], [], [], []
        for i in range(75, len(contents)):
            l = contents[i].split()
            freq.append(float(l[0]))
            S11.append(complex(float(l[1]), float(l[2])))
            S12.append(complex(float(l[3]), float(l[4])))
            S21.append(complex(float(l[5]), float(l[6])))
            S22.append(complex(float(l[7]), float(l[8])))
    S11, S12, S21, S22 = np.array(S11), np.array(S12), np.array(S21), np.array(S22)
    freq = np.array(freq)
    S11_dB = 20*np.log10(abs(S11))
    S12_dB = 20*np.log10(abs(S12))
    S21_dB = 20*np.log10(abs(S21))
    S22_dB = 20*np.log10(abs(S22))
    
    print(len(S11_dB), S11_dB)
    fig, ax = plt.subplots(1,1)
    ax.plot(freq, S11_dB, label = 'S11')
    ax.plot(freq, S12_dB, label = 'S12')
    ax.plot(freq, S22_dB, label = 'S22')
    ax.set_title(fname)
    #traces.TraceWater(freq, array([S11_dB, S22_dB, S12_dB]))
    ax.legend()
    
    return [freq, np.array(S11), np.array(S12), np.array(S21), np.array(S22)]

def calibration_sequence():
    
    check1 = raw_input("Parametres d'acquisition (nombre de points, plage de frequence, bandwidth), cables branches, canne correctement thermalisee ?\n\n Answer:[y]/n ")
    
    if check1 == "n":
        print "Corrigez les erreurs et relancez le script."
        return "ERROR"
    elif check1 == "y" or  check1 == "":
        pass
    else:
        print "Mauvais input: répondre par \"y\" (ou Enter) ou par \"n\". Relancez le script."
        return None
    
    check2 = str(raw_input("\n\n\nConfirmez la configuration des switchs:\n Port 1 / Switch 61: \n61.1 - Through \n61.2 - Top Sample C2 ou C7 \n61.3 - Top Sample C1 ou C8 \n61.4 - Open \n61.5 - Short \n61.6 - Match \n\n Port 2 / Switch 60: \n60.1 - Through \n60.2 - Match \n60.3 - Short \n60.4 - Bottom Sample C3 ou C6 \n60.5 - Open \n60.6 - Bottom Sample C4 ou C5 \n\n Answer:[y]/n "))
    
    if check2 == "n":
        print "Veuillez modifier ce code."
        return None
    elif check2 == "y" or  check2 == "":
        pass
    else:
        print "Mauvais input: répondre par \"y\" (ou Enter) ou par \"n\". Relancez le script."
        return None
    
    calibrationDone = False    
    
    while( not calibrationDone ):
        all_open()
        print "Beginning new step: all switch opened"
        check = str(raw_input("\nChoisissez une étape de calibration:  open  short  match  through  end\n\n Answer: "))
        
        if check == "open":
            print "Closing switch 61.4 and 60.5"
            dev.set_switch(61, 4, "close")
            dev.set_switch(60, 5, "close")
            print "Switch in Open config"
        
        elif check == "short":
            print "Closing switch 61.5 and 60.3"
            dev.set_switch(61, 5, "close")
            dev.set_switch(60, 3, "close")
            print "Switch in Short config"
            
        elif check == "match":
            print "Closing switch 61.6 and 60.2"
            dev.set_switch(61, 6, "close")
            dev.set_switch(60, 2, "close")
            print "Switch in Match config"
            
        elif check == "through":
            print "Closing switch 61.1 and 60.1"
            dev.set_switch(61, 1, "close")
            dev.set_switch(60, 1, "close")
            print "Switch in Through config"
        
        elif check == "end":
            calibrationDone = True
            
        else:
            print "Input incorrect. Veuillez choisir une des options proposées (\"open\", \"short\", \"match\", \"through\", \"end\")"
        
        raw_input("Press Enter to go to next step\n")
    
    print "Calibration completed. Exiting script."
    
    return True

def sweep_sequence(n_pts = 0, f_start = 0, f_stop = 0, bw = 0, temp = '4K', cal = 'True', power = [-20,-10,10]):
    fname24 = 'n35_Sp_1u_W_5u_' + temp + '_power_'
    fname36 = 'n35_Sp_1u_W_4u_' + temp + '_power_'
    check1 = str(raw_input("Noms et emplacements des fichiers et paramètres de puissance choisis dans ce script corrects ?\n Sample 61.2-60.4: {}\n Sample 61.3-60.6: {}\n Save location: {}\n Answer:[y]/n ".format(fname24,fname36, os.getcwd())))
    if check1 == "n":
        print "Veuillez recommencer."
        return "ERROR"
    elif check1 == "y" or  check1 == "":
        pass
    else:
        print "Mauvais input: répondre par \"y\" (ou Enter) ou par \"n\". Relancez le script."
        return None
        
    if n_pts == 0:
        n_pts = get(vna.npoints)
    else:
        set(vna.npoints, n_pts)

    if f_start == 0:
        f_start = get(vna.freq_start)
    else:
        set(vna.freq_start, f_start)

    if f_stop == 0:
        f_stop = get(vna.freq_stop)
    else:
        set(vna.freq_stop, f_stop)

    if bw == 0:
        bw = get(vna.bandwidth)
    else:
        set(vna.bandwidth, bw)

    print "Sweep parameters:\n n_pts = {}\n f_start = {}GHz\n f_stop = {}GHz\n bandwidth = {}".format(n_pts, round(f_start/1e9, 3), round(f_stop/1e9, 3), bw)
    print 'Using power = {}'.format(power)

    for i in power:
        set(vna.port_power_level_dBm, i)
        
        all_open()
        dev.set_switch(61,2,'close')
        dev.set_switch(60,4,'close')
        wait(10)
        get(vna.readval,filename = fname24 + str(i) + '_Top_Bop_%T.txt' )
        print "Power = {}, first sample done".format(i)
        
        all_open()
        dev.set_switch(61,3,'close')
        dev.set_switch(60,6,'close')
        wait(10)
        get(vna.readval,filename = fname36 + str(i) + '_Top_Bop_%T.txt')    
        print "Power = {}, 2nd sample done".format(i)
        
        all_open()
    print "All done."


def sweep_sequence_debug(n_pts = 3000, f_start = 1e8, f_stop = 1e10, bw = 200, localParams = True, temp = '4K', cal = 'True', power = [-20,-10,10]):
    fname24 = 'n35_Sp_1u_W_2u_' + temp + '_cal_' + cal + '_power_'
    fname36 = 'n35_Sp_1u_W_3u_' + temp + '_cal_' + cal + '_power_'
    check1 = str(raw_input("Noms et emplacements des fichiers et paramètres de puissance choisis dans ce script corrects ?\n Sample 61.2-60.4: {}\n Sample 61.3-60.6: {}\n Save location: {}\n Answer:[y]/n ".format(fname24,fname36, os.getcwd())))
    if check1 == "n":
        print "Veuillez recommencer."
        return "ERROR"
    elif check1 == "y" or  check1 == "":
        pass
    else:
        print "Mauvais input: répondre par \"y\" (ou Enter) ou par \"n\". Relancez le script."
        return None
        
    if localParams:
       n_pts, f_start, f_stop, bw = get(vna.npoints), get(vna.freq_start), get(vna.freq_stop), get(vna.bandwidth)
       print "Using sweep parameters as set currently in VNA config"
    else:
        print "Using sweep parameters as set by this script's parameters."
        set(vna.npoints, n_pts)
        set(vna.freq_stop, f_stop)
        set(vna.freq_start, f_start)
        set(vna.bandwidth, bw)
    print "Sweep parameters:\n n_pts = {}\n f_start = {}GHz\n f_stop = {}GHz\n bandwidth = {}".format(n_pts, round(f_start/1e9, 3), round(f_stop/1e9, 3), bw)
    print 'Using power = {}'.format(power)

    for i in power:
        set(vna.port_power_level_dBm,i)
        
        all_open()
        dev.set_switch(61,2,'close')
        dev.set_switch(60,4,'close')
        wait(10)
        get(vna.readval,filename = fname24 + str(i) + '_Top_Bop_%T.txt' )
        print "Power = {}, first sample done".format(i)
        
        all_open()
        dev.set_switch(61,3,'close')
        dev.set_switch(60,6,'close')
        wait(10)
        get(vna.readval,filename = fname36 + str(i) + '_Top_Bop_%T.txt')    
        print "Power = {}, 2nd sample done".format(i)
        
        all_open()
    print "All done."

def span_sequence(n_pts = 3000, f_center = 2e9, f_span = 2e9, bw = 200, localParams = False):
    
    fname24 = 'n15_Sp_1.5u_W_1u_hot_power_'
    fname36 = 'n15_Sp_0.8u_W_1u_hot_power_'
    check1 = str(raw_input("Noms et emplacements des fichiers et paramètres de puissance choisis dans ce script corrects ?\n Sample 61.2-60.4: {}\n Sample 61.3-60.6: {}\n Answer:[y]/n ".format(fname24,fname36)))
    if check1 == "n":
        print "Veuillez recommencer."
        return "ERROR"
    elif check1 == "y" or  check1 == "":
        pass
    else:
        print "Mauvais input: répondre par \"y\" (ou Enter) ou par \"n\". Relancez le script."
        return None
        
    if localParams:
       n_pts, f_center, f_span, bw = get(vna.npoints), get(vna.freq_center), get(vna.freq_span), get(vna.bandwidth)
       print "Using sweep parameters as set currently in VNA config"
    else:
        print "Using sweep parameters as set by this script's parameters."
        set(vna.npoints, n_pts)
        set(vna.freq_center, f_center)
        set(vna.freq_span, f_span)
        set(vna.bandwidth, bw)
    print "Sweep parameters:\n n_pts = {}\n f_center = {}Ghz\n f_span = {}Ghz\n bandwidth = {}".format(n_pts, round(freq_center/1e9, 3), round(freq_span/1e9, 3), bw)
    
    power = [-20, -10, 10]
    for i in power:
        set(vna.port_power_level_dBm,i)
        
        all_open()
        dev.set_switch(61,2,'close')
        dev.set_switch(60,4,'close')
        wait(10)
        get(vna.readval,filename='n15_Sp_1.5u_W_1u_hot_power_'+str(i)+'_Top_Bop_%T.txt')
        print "Power = {}, first sample done".format(i)
        
        all_open()
        dev.set_switch(61,3,'close')
        dev.set_switch(60,6,'close')
        wait(10)
        get(vna.readval,filename='n15_Sp_0.8u_W_1u_hot_power_'+str(i)+'_Top_Bop_%T.txt')    
        print "Power = {}, 2nd sample done".format(i)
        
        all_open()
    print "All done."

    