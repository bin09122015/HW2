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

def detect_change(base, target):
  (left, right) = get_confidence_interval(base)
  target_mean = sum(target)/len(target)

  # print ("(" + str(left) + "," + str(right) + ")", str(target_mean))
  (mean_cntr, var_cntr, std_cntr) = sp.stats.bayes_mvs(base, alpha=0.95)
  target_variance = (np.std(target, ddof=1))**2
  print ("(" + str(var_cntr[1][0]) + "," + str(var_cntr[1][1]) + ")", str(target_variance))

  return target_variance < var_cntr[1][0] or target_variance > var_cntr[1][1]

  return target_mean < left or target_mean > right

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
  print (target)

  starting += 1

  return starting

def run(dirname, file):
  assert BASE_COUNT >= WINDOW_LEN

  print (file)

  f = open(dirname + '/' + file)
  tmp_entries = []

  for i in range(BASE_COUNT):
    entry = get_next_entry(f)
    tmp_entries.append(entry)

  if isinstance(tmp_entries[0], float):
    base_window = tmp_entries[-WINDOW_LEN:]
    target_window = tmp_entries[-WINDOW_LEN:]
    starting_location = 0
    start_change = -1

    while True:
      new_entry = get_next_entry(f)
      if new_entry == "":
        break;

      starting_location = move_windows(base_window,
                                       target_window,
                                       starting_location,
                                       new_entry)
      if detect_change(base_window, target_window):
        if start_change == -1:
          start_change = starting_location + WINDOW_LEN - 1
        if starting_location >= start_change:
          print (start_change, starting_location)
          break
        print (start_change, starting_location)
      else:
        if start_change != -1:
          start_change = -1
    
    if start_change != -1 and (starting_location-start_change) < WINDOW_LEN/2:
        print (start_change, starting_location)
  else:
    print ("Categorical data should go here")

def main(argv):
  len_argv = len(argv)
  if len_argv != 1 and len_argv != 2:
    print ('runme.py <dirname> [filename]')
    sys.exit()

  dirname = argv[0]

  if len_argv == 1:
    for file in os.listdir("./" + dirname):
      if file.endswith(".txt"):
        run(dirname, file)
  else:
    assert len_argv == 2
    filename = argv[1]
    run(dirname, filename)

if __name__ == "__main__":
  main(sys.argv[1:])

