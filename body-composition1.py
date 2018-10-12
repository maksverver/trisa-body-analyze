#!/usr/bin/env python

# Based on logic from:
# class com.lifesense.fat.a (implements com.lifesense.fat.localFatPercentage)
# method com.lifesense.ble.LsBleManager$parseAdiposeData

def getBmi(weight_kg, height_m):
  return weight_kg / height_m / height_m

def getImp(resistance):
  if resistance < 410:
    return 3.0
  return 0.3 * (resistance - 400)

def getFat(sex, imp, age, bmi, mysteryBool):
  if mysteryBool:
    if sex == 0:
        return bmi * (1.504 + 3.835e-4 * imp) + 0.102 * age - 26.565
    if sex == 1:
        return bmi * (1.511 + 3.296e-4 * imp) + 0.104 * age - 17.241
  else:
    if sex == 0:
      return bmi * (1.479 + 4.4e-4 * imp) + 0.1 * age - 21.764
    if sex == 1:
      return bmi * (1.506 + 3.908e-4 * imp) + 0.1 * age - 12.834
  return 0.0

def getBodyWater(sex, imp, age, bmi, mysteryBool):
  if mysteryBool:
    if sex == 0:
      return 91.305 + (-1.191 * bmi - 0.00768 * imp + 0.08148 * age)
    if sex == 1:
      return 80.286 + (-1.132 * bmi - 0.0052 * imp + 0.07152 * age)
  else:
    if sex == 0:
      return 87.51 + (-1.162 * bmi - 0.00813 * imp + 0.07594 * age)
    if sex == 1:
      return 77.721 + (-1.148 * bmi - 0.00573 * imp + 0.06448 * age)

def getMuscle(sex, imp, age, bmi, mysteryBool):
  if mysteryBool:
    if sex == 0:
      return 77.389 + (-0.819 * bmi - 0.00486 * imp - 0.382 * age)
    if sex == 1:
      return 59.225 + (-0.685 * bmi - 0.00283 * imp - 0.274 * age)
  else:
    if sex == 0:
      return 74.627 + (-0.811 * bmi - 0.00565 * imp - 0.367 * age)
    if sex == 1:
      return 57.0 + (-0.694 * bmi - 0.00344 * imp - 0.255 * age)

def getBone(sex, imp, age, bmi, mysteryBool):
  if mysteryBool:
    if sex == 0:
      return 8.091 + (-0.0856 * bmi - 5.25e-4* imp - 0.0403 * age)
    if sex == 1:
      return 8.309 + (-0.0965 * bmi - 4.02e-4* imp - 0.0389 * age)
  else:
    if sex == 0:
      return 7.829 + (-0.0855 * bmi - 5.92e-4* imp - 0.0389 * age)
    if sex == 1:
      return 7.98 + (-0.0973 * bmi - 4.84e-4* imp - 0.036 * age)

age = 36
sex = 0  # male
height = 1.86
weight = 76.0
resistance = 538.60

for mystery_bool in [False, True]:
  bmi = getBmi(weight, height)
  imp = getImp(resistance)  # impedance?
  fat = getFat(sex, imp, age, bmi, mystery_bool)
  water = getBodyWater(sex, imp, age, bmi, mystery_bool)
  muscle = getMuscle(sex, imp, age, bmi, mystery_bool)
  bone = getBone(sex, imp, age, bmi, mystery_bool)
  print('mystery_bool:', mystery_bool)
  print('bmi:', bmi)
  print('fat:', fat)
  print('water:', water)
  print('muscle:', muscle)
  print('bone:', bone)
  print('')
