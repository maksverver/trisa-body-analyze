#!/usr/bin/env python

# Based on logic from:
# class com.lifesense.ble.commom.DataTranslateUtil

def getBmi(weight_kg, height_m):
  return weight_kg / height_m / height_m

def getBasalMetabolism(weight, age, muscleMass, sex):
  if sex == 0:
    return -72.421 + 30.809 * muscleMass + 1.795 * weight - 2.444 * age
  if sex == 1:
    return -40.135 + 25.669 * muscleMass + 6.067 * weight - 1.964 * age
  return 0.0

def getMuscle(weight, fatPercent, sex):
  if sex == 0:
      return 0.95 * weight - weight * (0.0095 * fatPercent) - 0.13
  if sex == 1:
      return 1.13 + 0.914 * weight - weight * (0.00914 * fatPercent)
  return 0.0

def getBodyWater(weight, resistance, height, sex):
  i = resistance - 10
  if sex == 0:
    result = 30.849 + height * (259672.5 * height) / weight / i + 0.372 * i / height / weight - weight * (2.581 * height) / i
  elif sex == 1:
    result = 23.018 + height * (201468.7 * height) / weight / i + 421.543 / weight / height + 160.445 * height / weight
  else:
    return 0.0
  if result < 30.0:
    result = 30.0
  return result

def getBone(muscleMass, sex):
  if sex == 0:
    return 0.116 + 0.0525 * muscleMass
  if sex == 1:
    return -1.22 + 0.0944 * muscleMass

def getFat(weight, resistance, height, age, sex):
  if resistance <= 0.0:
    return 0.0

  i = resistance - 10.0
  if sex == 0:
    result = (60.3
        - height * (486583.0 * height) / weight / i
        + 9.146 * weight / height / height / i
        - height * (251.193 * height) / weight / age
        + 1625303.0 / i / i
        - 0.0139 * i
        + 0.05975 * age)
  if sex == 1:
    result = (57.621
        - height * (186.422 * height) / weight
        - height * (382280.0 * height) / weight / i
        + 128.005 * weight / height / i
        - 0.0728 * weight / height
        + 7816.359 / height / i
        - 3.333 * weight / height / height / age)
  return max(5.0, result)

age = 36
sex = 0  # male
height = 1.86
weight = 76.0
resistance = 538.60

bmi = getBmi(weight, height)
fat = getFat(weight, resistance, height, age, sex)
water = getBodyWater(weight, resistance, height, sex)
muscle = getMuscle(weight, fat, sex)
bone = getBone(muscle, sex)
calorie = getBasalMetabolism(weight, age, muscle, sex)
print('bmi:', bmi)
print('fat:', fat)
print('water:', water)
print('muscle:', muscle)
print('bone:', bone)
print('calorie:', calorie)
