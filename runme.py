from __future__ import division
from scipy.stats import chisquare, chi2_contingency, binom_test

import sys
import os

import numpy as np
import scipy as sp
from scipy import stats

import warnings
warnings.filterwarnings("ignore")

BASE_COUNT = 50
WINDOW_LEN = 50
DEBUG = False

def get_confidence_interval(data, confidence=0.95):
  a = np.array(data)
  n = len(a)
  m = np.mean(a)

  sigma = sp.stats.sem(a)
  h = sigma * sp.stats.t._ppf((1+confidence)/2, n-1)

  return m-h, m+h

def detect_mean_change(base, target):
  (left, right) = get_confidence_interval(base)
  target_mean = sum(target)/len(target)

  if DEBUG:
    print ("mean: (" + str(left) + "," + str(right) + ")", str(target_mean))

  return target_mean < left or target_mean > right

def detect_var_change(base, target):
  (mean_cntr, var_cntr, std_cntr) = sp.stats.bayes_mvs(base, alpha=0.95)
  target_variance = (np.std(target, ddof=1))**2

  if DEBUG:
    print ("variance: (" + str(var_cntr[1][0]) + "," + str(var_cntr[1][1]) + ")", str(target_variance))

  return (target_variance < var_cntr[1][0], target_variance > var_cntr[1][1])

def get_next_entry(f):
  entry = f.readline()
  if entry == "":
    return None

  entry = entry.strip()
  try:
    number = float(entry)
    return number
  except ValueError:
    return entry

def slide_window(window, new_element):
  window.pop(0)
  window.append(new_element)

def move_windows(base, target, starting, new_entry):
  if starting >= BASE_COUNT:
    slide_window(base, target[0])
    if DEBUG:
      print (base)

  slide_window(target, new_entry)
  if DEBUG:
    print (target)

  starting += 1

  return starting

def backtrace(target, base, start_var_change, starting_location):
  result = start_var_change

  target = target[::-1]
  base = base[::-1]

  (_, var_cntr, _) = sp.stats.bayes_mvs(target, alpha=0.95)
  while len(base)>0:
    target.pop(0)
    target.append(base[0])
    base.pop(0)
    starting_location -= 1

    if starting_location < BASE_COUNT:
      return result

    target_variance = (np.std(target, ddof=1))**2

    if DEBUG:
      print ("back variance: (" + str(var_cntr[1][0]) + "," + str(var_cntr[1][1]) + ")", str(target_variance))

    if (target_variance > var_cntr[1][1]):
      result = starting_location + 1
      break

  return result

def run(dirname, file):
  f = open(dirname + '/' + file)
  first_entry = get_next_entry(f)
  f.close()
  
  print ("Processing " + file)

  if isinstance(first_entry, float):
    
    assert BASE_COUNT >= WINDOW_LEN
  
    f = open(dirname + '/' + file)
    tmp_entries = []
  
    for i in range(BASE_COUNT):
        entry = get_next_entry(f)

        if entry is None:
          return (file, "not sufficient baseline.")
        if not isinstance(entry, float):
          return (file, "encounter non-numeric data in a numberic test file.")

        tmp_entries.append(entry)
  
    base_window = tmp_entries[-WINDOW_LEN:]
    target_window = tmp_entries[-WINDOW_LEN:]
    starting_location = 0
    start_mean_change = -1
    start_var_change = -1

    result = -1
    lt = False
    gt = False

    while True:
      new_entry = get_next_entry(f)
      if new_entry == None or new_entry == "":
        break;
      if not isinstance(new_entry, float):
        return (file, "encounter non-numeric data in a numberic test file.")

      starting_location = move_windows(base_window,
                                       target_window,
                                       starting_location,
                                       new_entry)
      if detect_mean_change(base_window, target_window):
        if start_mean_change == -1:
          start_mean_change = starting_location + WINDOW_LEN - 1
        if starting_location >= start_mean_change:
          result = start_mean_change
          if DEBUG:
            print ("mean_b", start_mean_change, starting_location)
          start_mean_change = -1
          break
  
        if DEBUG:
          print ("mean", start_mean_change, starting_location)
      else:
        if start_mean_change != -1:
          start_mean_change = -1

      (lt, gt) = detect_var_change(base_window, target_window)

      if lt or gt:
        if start_var_change == -1:
          start_var_change = starting_location + WINDOW_LEN - 1
        if start_mean_change == -1 and starting_location >= start_var_change:
          if lt:
            start_var_change = backtrace(target_window, base_window, start_var_change, starting_location)
          result = start_var_change
          if DEBUG:
            print ("var_b", start_var_change, starting_location)
          start_var_change = -1
          break

        if DEBUG:
          print ("var", start_var_change, starting_location)
      else:
        if start_var_change != -1:
          start_var_change = -1
    
    if start_mean_change != -1 and (start_mean_change-starting_location) < WINDOW_LEN/2:
        result = start_mean_change
        if DEBUG:
          print ("mean_e", start_mean_change, starting_location)

    if result == -1 and start_var_change != -1 and (start_var_change-starting_location) < WINDOW_LEN/2:
        if lt:
          start_var_change = backtrace(target_window, base_window, start_var_change, starting_location)

        result = start_var_change
        if DEBUG:
          print ("var_e", start_var_change, starting_location)

    f.close()

    return (file, str(result))
  
  else:
  
    # Categorical data should go here
    
    dirAndFile = dirname + '/' + file
    
    data = readData(dirAndFile)

    result = detectChange_Categoral(threshold=0.0005, WINDOW_LEN = 40, MOVING_INTERVAL = 5, data=data)
    
    if DEBUG:
      print(file, result)

    return (file, str(result))

def readData(file):
    fin = open(file, 'r')
    data = fin.read()
    fin.close()

    data = list(map(lambda s: s.strip(), data))  # remove '/n'
    data = list(filter(None, data))  # remove empty string
    
    return data

def detectChange_Categoral(threshold, WINDOW_LEN, MOVING_INTERVAL, data):
    baseline = data[0:BASE_COUNT]

    variables = list(set(baseline))
    
    freq_old = np.zeros(len(variables))
    freq = np.zeros(len(variables))

    k = 0
    while (k + 2 * WINDOW_LEN < len(data)):
        
        p = calculateP(variables, k, data, WINDOW_LEN)

        
        if(k + WINDOW_LEN > 50 and p < threshold):
            start = k + WINDOW_LEN            
            for i in range(WINDOW_LEN):
                k_track = start - WINDOW_LEN - i
                p_track = calculateP(variables, k_track, data, WINDOW_LEN)
                if(p_track > 0.05):
                    break
            
            end = k_track + 2*WINDOW_LEN
            position = int((start + end)/2)
            return position

        k = k + MOVING_INTERVAL        
    
    return -1
    
    
def calculateP(variables, k, data, WINDOW_LEN):
    
    freq_old = np.zeros(len(variables))
    freq = np.zeros(len(variables))

    for i in range(len(variables)):
        sample = data[k:k+WINDOW_LEN]
        freq_old[i] = sample.count(variables[i])

        sample = data[k+WINDOW_LEN : k+2*WINDOW_LEN]
        freq[i] = sample.count(variables[i])

    if (len(variables)==2):
        chi = chisquare(freq, freq_old)
        p = chi[1]
        # Tried the exact binomial goodness of fit method:
        # p = binom_test(freq, n=None, p=freq_old[0]/sum(freq_old))
        # The results were the same as Chi-square
    else:    
        if (sum(freq==0)>0 or sum(freq_old==0)>0):
            chi = chisquare(freq, freq_old)
        else:
            chi = chi2_contingency([freq,freq_old], correction=True)
        p = chi[1]
        
    return p


def main(argv):
  len_argv = len(argv)
  if len_argv != 1 and len_argv != 2:
    print ('runme.py <dirname> [filename]')
    sys.exit()

  dirname = argv[0]
  output = []

  if len_argv == 1:
    for file in os.listdir("./" + dirname):
      if file.endswith(".txt"):
        result = run(dirname, file)
        output.append(result)
  else:
    assert len_argv == 2
    filename = argv[1]
    result = run(dirname, filename)
    output.append(result)

  f = open("outputbin.txt", "w")
  f.write("Bin Gao" + "\t" + "Bin Yan" + "\n")
  for (filename, position) in output:
    f.write(filename + "\t" + position + "\n")
  f.close()

if __name__ == "__main__":
  main(sys.argv[1:])

