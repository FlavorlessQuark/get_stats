import re
import json
from math import log10
from functools import reduce
import requests

MAX = log10(104019552000000000000000000000000000000)
VAL = 44226000000000000000000000000000000000
MIN = log10(29663085937500.0)

RANGE = MAX - MIN
NRANGE = 10 - 1

with open("./jesus.txt") as input:
	doc =  input.read()

with open("./nft.txt") as input:
	nft =  input.read()

exp = re.findall('(.* = \[.*\])\n(.* = \[.*\])\n\n', doc)

dic = {}
maxVals = []
minVals = []
gear_stats = {}
gear_minmax = {}
gear = ["Left hand item", "Right hand item", "Boots/leg gadgets", "Gloves/gadgets", "Hat/Hair", "Armor", "Jumpsuit"]
gear_ranges = [
			[(1, 3), (1, 2), (0, 0)], #lhi
			[(1, 3), (1, 2), (0, 0)], #rhi
			[(0, 2), (0, 0), (0, 2)], #boots
			[(0, 2), (0, 0), (0, 2)], #glove
			[(0, 0), (0, 0), (0, 1)], #head
			[(0, 0), (1, 3), (0, 1)], #armor
			[(0, 1), (0, 1), (0, 1)] #jupsuit
			] # Format [[(atk_low, atk_high), (def_low, def_high), (heal_low, heal_high)], [...], ...]


def scaleNum(num, ran, nrange):
	return (((num - ran[1]) * -(nrange[1] - nrange[0])) / (ran[1] - ran[0])) + nrange[0]

def item_stats(slot, item, ranges):
	stats = [0, 0, 0]

	stats[0] = round(scaleNum(dic[slot][item], (gear_minmax[slot][0], 100), (ranges[0][0], ranges[0][1])), 1)
	stats[1] = round(scaleNum(dic[slot][item], (gear_minmax[slot][0], 100), (ranges[1][0], ranges[1][1])), 1)
	stats[2] = round(scaleNum(dic[slot][item], (gear_minmax[slot][0], 100), (ranges[2][0], ranges[2][1])), 1)
	return stats


for lines in exp:
	p1 = re.findall('(.*) = (\[.*\])', lines[0])
	p2 = re.findall('(.*) = (\[.*\])', lines[1])
	# print("LINE", p2[0][1])
	names = eval(p1[0][1])
	rarities = eval(p2[0][1])

	dic[p1[0][0]] = {names[i] : rarities[i] if rarities[i] > 0 else 100 for i, _ in enumerate(names)}
	if ((p1[0][0][2:]) in gear):
		if ("None" in dic[p1[0][0]]):
			r = sorted(rarities)
			gear_minmax[p1[0][0]] = (r[0], r[-2])
		else:
			gear_minmax[p1[0][0]] = (min(rarities), max(rarities))
	# print("Values ", eval(p2[0][1]))
	maxVals.append(max(eval(p2[0][1])))
	minVals.append(min(eval(p2[0][1])))

# print(minVals, maxVals)



#------------ Compute item stats ----------------------------

for i, slot in enumerate(gear):
	# gear_stats["m_" + slot] = {}
	tmp_stats = {}
	# print(slot, gear_minmax)
	for item in dic["m_" + slot]:
		tmp_stats[item] = [0, 0, 0]
		# print(slot, item, i, gear_ranges[i])
		if (item != "None"):
			tmp_stats[item] = item_stats("m_" + slot, item, gear_ranges[i])
		if ("shield" not in item and (gear[0] in slot or gear[1] in slot)):
			tmp_stats[item][1] = 0
	gear_stats["m_" + slot] = tmp_stats
	for item in dic["f_" + slot]:
		tmp_stats[item] = [0, 0, 0]
		# print(slot, item, i, gear_ranges[i])
		if (item != "None"):
			tmp_stats[item] = item_stats("f_" + slot, item, gear_ranges[i])
		if ("shield" not in item and (gear[0] in slot or gear[1] in slot)):
			tmp_stats[item][1] = 0
	gear_stats["f_" + slot] = tmp_stats

# print(gear_minmax)
# print(gear_stats)

f = []

for n in range(1001, 1004):
	r = requests.get("https://blockduelers.mypinata.cloud/ipfs/QmWku4hUmzuom5Xit8GUak3MWTVvGDfHXN7NCaJELfRSoQ/" + str(n))

	nft = r.json()
	print(n)
	# nft = eval(nft)

	# Do this for every NFT
	# Sanitize input

	vals = []
	s_nftAttrs = {}
	prefix = ""

	# print("NFT", n, nft)
	# print(dic)

	# Dueler Rairity
	for attr in nft["attributes"]:

		if (attr["trait_type"] == "Gender"):
			prefix = "m_" if attr["value"] == "Male" else "f_"
		elif (attr["trait_type"] != "Background" and attr["trait_type"] != "Frame"):
			if ("Glov" in attr["trait_type"]):
				s_nftAttrs[prefix + 'Gloves/gadgets'] = attr["value"]
			else:
				s_nftAttrs[prefix + attr["trait_type"]] = attr["value"]
		else :
			s_nftAttrs[attr["trait_type"]] = attr["value"]


	nftRarity = reduce(lambda x, y: x * y, [dic[att][s_nftAttrs[att]] for att in s_nftAttrs])
	# if (nftRarity == 0):
	# 	nftRarity = log10(1)
	# else:
	# 	nftRarity = log10(nftRarity)

	rarity = (((log10(nftRarity ) - MAX) * - NRANGE) / RANGE) + 1
	rarity = round(rarity, 0)

	nftStats = [0, 0, 0]
	lhi = (0, 0)
	rhi = (0, 0)
	for att in s_nftAttrs:
		if (att in gear_stats):
			if (att[2:] == gear[0]):
				lhi = (gear_stats[att][s_nftAttrs[att]][0], dic[att][s_nftAttrs[att]])
			elif (att[2:] == gear[1]):
				rhi = (gear_stats[att][s_nftAttrs[att]][0], dic[att][s_nftAttrs[att]])
			else:
				nftStats[0] += gear_stats[att][s_nftAttrs[att]][0]
			nftStats[1] += gear_stats[att][s_nftAttrs[att]][1]
			nftStats[2] += gear_stats[att][s_nftAttrs[att]][2]

	if (lhi[1] > rhi[1]):
		nftStats[0] += ((lhi[0] / 100 )* 75) + ((rhi[0] / 100 )* 25)
	else :
		nftStats[0] += ((rhi[0] / 100 )* 75) + ((lhi[0] / 100 )* 25)

	nftStats[0] = nftStats[0] + 1 if nftStats[0] < 1 else nftStats[0]
	nftStats[1] = nftStats[1] + 1 if nftStats[1] < 1 else nftStats[1]
	nftStats[2] = nftStats[2] + 1 if nftStats[2] < 1 else nftStats[2]
			# print(gear_stats[att][s_nftAttrs[att]])
	# print("NFT rarity %d | Stats ATK : %d DEF : %d  HEAL : %d"% (rarity, nftStats[0], nftStats[1], nftStats[2]))
	# print(nftRarity, round(rarity, 0), rarity)
	NFT = {
		"name": nft["name"],
		"picture":nft["image"],
		"baseStats": {
			"attack": nftStats[0],
			"defense": nftStats[1],
			"heal" : nftStats[2]
			},
		"rarity": rarity
		}
	f.append(NFT)

# print(f)

with open('data.json', 'w') as file:
	json.dump(gear_stats, file)

# # print("FOUND", exp[1])
# # print("DATA", exp1)
# # print("MAXS", maxVals, reduce(lambda x, y: x * y, [1,5,10]))
# print("MAXS", maxVals, reduce(lambda x, y: x * y, maxVals))
# print("MINS", minVals,reduce(lambda x, y: (1 if x == 0 else x)* (0.1 if y == 0 else y), minVals))
# # (.*) = (\[.*\])
# # Rarities : Add all values of NFT then scale between , min and max, then scale from 0 - 10
# # Atack values :
