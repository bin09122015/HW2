from __future__ import division
from scipy.stats import chisquare, chi2_contingency

import sys
import os

import numpy as np
import scipy as sp
from scipy import stats

BASE_COUNT = 50
WINDOW_LEN = 50

def get_confidence_interval(data, confidence=0.95):
  a = np.array(data)
  n = len(a)
  m = np.mean(a)
  # sigma = np.std(a, ddof=1)
  # conf_int = stats.norm.interval(confidence, loc=m, scale=sigma)

  sigma = sp.stats.sem(a)
  h = sigma * sp.stats.t._ppf((1+confidence)/2, n-1)

  return m-h, m+h

def detect_mean_change(base, target):
  (left, right) = get_confidence_interval(base)
  target_mean = sum(target)/len(target)

  # print ("mean: (" + str(left) + "," + str(right) + ")", str(target_mean))

  return target_mean < left or target_mean > right

def reject_outliers(data):
  return data

  tmp = data[:]
  tmp_max = max(tmp)
  tmp_min = min(tmp)
  tmp.remove(tmp_max)
  tmp.remove(tmp_min)

  assert len(tmp) == len(data)-2

  return tmp

def detect_var_change(base, target):
  base_minus_outliers = reject_outliers(base)
  (mean_cntr, var_cntr, std_cntr) = sp.stats.bayes_mvs(base_minus_outliers, alpha=0.95)
  target_minus_outliers = reject_outliers(target)
  target_variance = (np.std(target_minus_outliers, ddof=1))**2

  # print ("variance: (" + str(var_cntr[1][0]) + "," + str(var_cntr[1][1]) + ")", str(target_variance))

  return (target_variance < var_cntr[1][0], target_variance > var_cntr[1][1])

def get_next_entry(f):
  entry = f.readline().strip()
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
    # print (base)

  slide_window(target, new_entry)
  # print (target)

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

    target_variance = (np.std(target, ddof=1))**2

    # print ("back variance: (" + str(var_cntr[1][0]) + "," + str(var_cntr[1][1]) + ")", str(target_variance))

    if (target_variance > var_cntr[1][1]):
      result = starting_location + 1
      break

  return result

def run(dirname, file):
  f = open(dirname + '/' + file)
  first_entry = get_next_entry(f)
  f.close()
  
  if isinstance(first_entry, float):
    
    assert BASE_COUNT >= WINDOW_LEN
  
    print (file)
  
    f = open(dirname + '/' + file)
    tmp_entries = []
  
    for i in range(BASE_COUNT):
        entry = get_next_entry(f)
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
      if new_entry == "":
        break;

      starting_location = move_windows(base_window,
                                       target_window,
                                       starting_location,
                                       new_entry)
      if detect_mean_change(base_window, target_window):
        if start_mean_change == -1:
          start_mean_change = starting_location + WINDOW_LEN - 1
        if starting_location >= start_mean_change:
          result = start_mean_change
          print ("mean_b", start_mean_change, starting_location)
          start_mean_change = -1
          break
        # print ("mean", start_mean_change, starting_location)
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
          print ("var_b", start_var_change, starting_location)
          start_var_change = -1
          break
        # print ("var", start_var_change, starting_location)
      else:
        if start_var_change != -1:
          start_var_change = -1
    
    if start_mean_change != -1 and (start_mean_change-starting_location) < WINDOW_LEN/2:
        result = start_mean_change
        print ("mean_e", start_mean_change, starting_location)

    if result == -1 and start_var_change != -1 and (start_var_change-starting_location) < WINDOW_LEN/2:
        if lt:
          start_var_change = backtrace(target_window, base_window, start_var_change, starting_location)

        result = start_var_change
        print ("var_e", start_var_change, starting_location)

    f.close()

    return (file, result)
  
  else:
  
    # Categorical data should go here
    
    dirAndFile = dirname + '/' + file
    result = detectChange_Categoral(dirAndFile, threshold=0.0005, WINDOW_LEN = 40, MOVING_INTERVAL = 5)
    
    
    print(file, result)

    return (file, result)

def detectChange_Categoral(file, threshold, WINDOW_LEN, MOVING_INTERVAL):
    fin = open(file, 'r')
    data = fin.read()
    fin.close()

    data = list(map(lambda s: s.strip(), data))  # remove '/n'
    data = list(filter(None, data))  # remove empty string
    # data is a list now

    baseline = data[0:BASE_COUNT]

    variables = list(set(baseline))

    freq_old = np.zeros(len(variables))
    freq = np.zeros(len(variables))


    for i in range(len(variables)):
        freq_old[i] = baseline[0:WINDOW_LEN].count(variables[i])

    k = 0
    while (k + 2 * WINDOW_LEN < len(data)):
        for i in range(len(variables)):
            sample = data[k:k+WINDOW_LEN]
            freq_old[i] = sample.count(variables[i])

            sample = data[k+WINDOW_LEN : k+2*WINDOW_LEN]
            freq[i] = sample.count(variables[i])

        if (sum(freq==0)>0 or sum(freq_old==0)>0):
            chi = chisquare(freq, freq_old)
        else:
            chi = chi2_contingency([freq,freq_old], correction=True)
            
        if (len(variables)==2):
            chi = chisquare(freq, freq_old)
        

        if(k + WINDOW_LEN>50 and chi[1]<threshold):
            return k+WINDOW_LEN

        k = k + MOVING_INTERVAL
        freq_old = freq.copy()
        
    
    return -1


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
  for (filename, position) in output:
    f.write(filename + "\t" + str(position) + "\n")
  f.close()

if __name__ == "__main__":
  main(sys.argv[1:])

