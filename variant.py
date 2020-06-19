from cyvcf2 import VCF

class Variant:

    def __init__(self, variant, family, gnomAD_AF_Threshold, REVEL_Threshold, CSQList, matchingClinVarVariants):
        self.matchingClinVarVariants = matchingClinVarVariants
        self.variant = variant
        self.evidenceCodes = {"PVS1": 0, "PS1": 0, "PS2": 0, "PS3": 0, "PS4": 0, "PM1": 0, "PM2": 0, "PM3": 0, "PM4": 0, "PM5": 0, "PM6": 0, "PP1": 0, "PP2": 0, "PP3": 0, "PP4": 0, "PP5": 0, "BA1": 0, "BS1": 0, "BS2": 0, "BS3": 0, "BS4": 0, "BP1": 0, "BP2": 0, "BP3": 0, "BP4": 0, "BP5": 0, "BP6": 0, "BP7": 0}
        self.CSQList = CSQList
        self.CSQDict = self.getCSQDict(self.variant)

        self.position = self.variant.POS
        self.gnomad_popmax_af = 0
        self.PStCounts = 0
        self.PMCounts = 0
        self.PSuCounts = 0
        self.PVstCounts = 0
        self.BStCounts = 0
        self.BSuCounts = 0
        self.BAsCounts = 0
        self.gnomAD_AF_Threshold = gnomAD_AF_Threshold
        self.REVEL_Threshold = REVEL_Threshold
        self.family = family
        self.maternalGeno = self.variant.genotypes[self.family.getMaternalSample().sampleIdx]
        self.paternalGeno = self.variant.genotypes[self.family.getPaternalSample().sampleIdx]
        self.childGeno = self.variant.genotypes[self.family.getChildSample().sampleIdx]
        self.affectedGenos = self.getAffectedGenotypes()
        self.unaffectedGenos = self.getUnaffectedGenotypes()
        self.printVariant = True
        self.isCorrectlySegragated = self.checkIsCorrectlySegregated()

        if not self.areAllGenotypesValid():
            eprint("Invalid Genotype at ", self.variant.CHROM, std(position))
            self.printVariant = False
        elif len(self.affectedGenos) == 0 or self.childGeno.count('0') >= 2 or self.affectedsGenotypeMismatch():
            self.printVariant = False
        else:
            self.parseLine()

    def areAllGenotypesValid(self):
        for geno in self.variant.genotypes:
            if geno[0] == '.' or geno[1] == '.':
                return False
        return True

    def getAffectedGenotypes(self):
        affectedGenotypes = {}
        for affectedSample in self.family.getAllAffectedIndividuals():
            affectedGenotypes[affectedSample.individualID] = self.variant.genotypes[affectedSample.sampleIdx]
        return affectedGenotypes

    def getUnaffectedGenotypes(self):
        unaffectedGenotypes = {}
        for unaffectedSample in self.family.getAllUnaffectedIndividuals():
            unaffectedGenotypes[unaffectedSample.individualID] = self.variant.genotypes[unaffectedSample.sampleIdx]
        return unaffectedGenotypes

    def affectedsGenotypeMismatch(self):
        affectedGeno = ''
        for affectedSample in self.family.getAllAffectedIndividuals():
            if self.variant.genotypes[affectedSample.sampleIdx] != affectedGeno and affectedGeno != '':
                return True
            affectedGeno = self.variant.genotypes[affectedSample.sampleIdx]
        return False

    def checkValidAffectedAndUnaffectedGenoType(self):
        affectedGeno = list(self.affectedGenos.values())[0]
        # for geno in self.affectedGenos.values():
            # affectedGeno = geno
        # affectedGeno = self.affectedGenos.values()[0]
        for sampleGenotype in self.unaffectedGenos.values():
            if (sum(affectedGeno) == 1 and sum(sampleGenotype) == 0) or (sum(affectedGeno) == 2 and sum(sampleGenotype) == 1):
                return True
        return False

    def checkIsCorrectlySegregated(self):
        if (sum(self.childGeno) == 1 and (sum(self.maternalGeno) + sum(self.paternalGeno) == 1)):
            return True
        elif (sum(self.childGeno) == 2 and (sum(self.maternalGeno) >= 1 and sum(self.paternalGeno) >= 1)):
            return True
        else:
            return False

    def parseLine(self):
        if self.affectedsGenotypeMismatch():
            for code in self.evidenceCodes:
                self.evidenceCodes[code] = -1
        else:
            self.populateCSQ()
            self.processPVstCounts()
            self.processPStCounts()
            self.processPMCounts()
            self.processPSuCounts()

            self.processBAsCounts()
            self.processBStCounts()
            self.processBSuCounts()

    def getCSQDict(self, variant):
        CSQDict = {v:[] for i, v in enumerate(self.CSQList)} # produces a dictionary of empty arrays
        if variant.INFO.get("CSQ") != None:
            rawCSQ = [x.split('|') for x in variant.INFO.get("CSQ").split(',')]
            for csqIdx, csqKey in enumerate(self.CSQList):
                for csqList in rawCSQ:
                    CSQDict[csqKey].append(csqList[csqIdx])
        return CSQDict

    def processPVstCounts(self):
        # very strong PVS1
        highCount = self.CSQDict['IMPACT'].count("HIGH")
        if highCount > 0 and self.isCorrectlySegragated:
            self.PVstCounts = 1
            self.evidenceCodes["PVS1"] = 1
        else:
            self.evidenceCodes["PVS1"] = -1

    def processPStCounts(self):
        # strong PS1-PS4
        # Checking PS1
        self.evidenceCodes["PS1"] = 0
        if len(self.matchingClinVarVariants) > 0 and self.isCorrectlySegragated:
            for clinVarVariant in self.matchingClinVarVariants:
                if clinVarVariant.INFO.get('CLNSIG') is not None and clinVarVariant.INFO.get('CLNSIG').lower() == "pathogenic":
                    clinvarCSQDict = self.getCSQDict(clinVarVariant)
                    if clinvarCSQDict['Protein_position'] == self.CSQDict['Protein_position'] and clinvarCSQDict['Amino_acids'] == self.CSQDict['Amino_acids']:
                        self.evidenceCodes["PS1"] = 1
            if self.evidenceCodes["PS1"] != 1:
                self.evidenceCodes["PS1"] = -1
        # Checking PS2
        if (sum(self.childGeno) == 1 and sum(self.maternalGeno) == 0 and sum(self.paternalGeno) == 0):
            self.evidenceCodes["PS2"] = 1
        else:
            self.evidenceCodes["PS2"] = 0
        # Checking PS3
        self.evidenceCodes["PS3"] = 0
        # Checking PS4
        if self.checkValidAffectedAndUnaffectedGenoType():
            self.evidenceCodes["PS4"] = 1
        else:
            self.evidenceCodes["PS4"] = 0

    def processPMCounts(self):
        # moderate PM1-PM6
        # Checking PM1
        pfamCount = self.CSQDict['DOMAINS'].count("Pfam_domain")
        if self.isCorrectlySegragated and pfamCount > 0:
            self.evidenceCodes["PM1"] = pfamCount
        else:
            self.evidenceCodes["PM1"] = -1
        # Checking PM2
        if self.isCorrectlySegragated and self.gnomad_popmax_af < self.gnomAD_AF_Threshold:
            self.evidenceCodes["PM2"] = 1
        else:
            self.evidenceCodes["PM2"] = -1
        # Checking PM3
        self.evidenceCodes["PM3"] = 0
        # PM4 NA
        consequenceList = ['inframe_deletion', 'inframe_insertion', 'stop_lost']
        for consequence in self.CSQDict['Consequence']:
            if consequence in consequenceList:
                self.evidenceCodes["PM4"] = 1
        if not self.isCorrectlySegragated or self.evidenceCodes["PM4"] == 0:
            self.evidenceCodes["PM4"] = -1
        # PM5 NA
        self.evidenceCodes["PM5"] = 0
        if len(self.matchingClinVarVariants) > 0:
            for clinVarVariant in self.matchingClinVarVariants:
                if self.isCorrectlySegragated and clinVarVariant.INFO.get('CLNSIG') is not None and clinVarVariant.INFO.get('CLNSIG').lower() == "pathogenic":
                    clinvarCSQDict = self.getCSQDict(clinVarVariant)
                    if clinvarCSQDict['Protein_position'] == self.CSQDict['Protein_position'] and clinvarCSQDict['Amino_acids'] != self.CSQDict['Amino_acids']:
                        self.evidenceCodes["PM5"] = 1
            if self.evidenceCodes["PM5"] != 1:
                self.evidenceCodes["PM5"] = -1
        # exit(0)

        # PM6 NA
        self.evidenceCodes["PM6"] = 0

    def processPSuCounts(self):
        # supporting PP1-PP5
        # Checking PP1
        self.evidenceCodes["PP1"] = 0
        # Checking PP2
        self.evidenceCodes["PP2"] = 0
        # Checking PP3
        self.evidenceCodes["PP3"] = 0
        for revel in self.CSQDict['REVEL']:
            if self.isCorrectlySegragated and len(revel) > 0 and float(revel) > self.REVEL_Threshold:
                self.evidenceCodes["PP3"] = 1
        if self.evidenceCodes["PP3"] == 0:
            self.evidenceCodes["PP3"] = -1
        # Checking PP4
        self.evidenceCodes["PP4"] = 0
        # Checking PP5
        self.evidenceCodes["PP5"] = 0

    def processBAsCounts(self):
        # benign standalone BA1
        # Checking BA1
        if self.variant.INFO['gnomad_popmax_af'] > 0.05:
            self.evidenceCodes["BA1"] = 1
        else:
            self.evidenceCodes["BA1"] = -1

    def processBStCounts(self):
        # strong BS1-BS4
        # Checking BS1
        if self.isCorrectlySegragated and self.gnomad_popmax_af > self.gnomAD_AF_Threshold:
            self.evidenceCodes["BS1"] = 1
        else:
            self.evidenceCodes["BS1"] = -1
        # Checking BS2
        if self.isCorrectlySegragated:
            self.evidenceCodes["BS2"] = 1
        else:
            self.evidenceCodes["BS2"] = -1

        # Checking BS3
        self.evidenceCodes["BS3"] = 0
        # Checking BS4
        self.evidenceCodes["BS4"] = self.evidenceCodes["BS2"]

    def processBSuCounts(self):
        # supporting BP1-BP7
        # Checking BP1
        self.evidenceCodes["BP1"] = 0
        # Checking BP2
        self.evidenceCodes["BP2"] = 0
        # Checking BP3
        self.evidenceCodes["BP3"] = 0
        if (len(''.join(self.CSQDict['DOMAINS'])) == 0):
            consequenceList = ['inframe_deletion', 'inframe_insertion', 'stop_lost']
            for consequence in self.CSQDict['Consequence']:
                if self.isCorrectlySegragated and consequence in consequenceList:
                    self.evidenceCodes["BP3"] = 1
        if self.evidenceCodes["BP3"] == 0:
            self.evidenceCodes["BP3"] = -1
        # Checking BP4
        self.evidenceCodes["BP4"] = -1
        for revel in self.CSQDict['REVEL']:
            if self.isCorrectlySegragated and len(revel) > 0 and float(revel) < self.REVEL_Threshold:
                self.evidenceCodes["BP4"] = 1
                # Do we want to break here or keep counting?
        # Checking BP5
        self.evidenceCodes["BP5"] = 0
        # Checking BP6
        self.evidenceCodes["BP6"] = 0
        # Checking BP7
        self.evidenceCodes["BP7"] = self.CSQDict['Consequence'].count('synonymous_variant')# and self.CSQDict['Consequence'].count('splice_region')
        if self.isCorrectlySegragated and (self.evidenceCodes["BP7"] == 0 or (len(''.join(self.CSQDict['DOMAINS'])) > 0)):
            self.evidenceCodes["BP7"] = -1

    def getEvidenceCodesString(self):
        codesOrder = ["PVS1", "PS1", "PS2", "PS3", "PS4", "PM1", "PM2", "PM3", "PM4", "PM5", "PM6", "PP1", "PP2", "PP3", "PP4", "PP5", "BA1", "BS1", "BS2", "BS3", "BS4", "BP1", "BP2", "BP3", "BP4", "BP5", "BP6", "BP7"]
        codes = []
        for code in codesOrder:
            codes.append(code + "=" + str(self.evidenceCodes[code]))
        return ';'.join(codes)

    def populateCSQ(self):
        #Location|Allele|SYMBOL|IMPACT|Consequence|Protein_position|Amino_acids|Existing_variation|IND|ZYG|ExACpLI|REVEL|DOMAINS|CSN|PUBMED
        idxs = ['Location', 'Allele', 'SYMBOL', 'IMPACT', 'Consequence', 'Protein_position', 'Amino_acids', 'Existing_variation', 'IND', 'ZYG', 'ExACpLI', 'REVEL', 'DOMAINS', 'CSN', 'PUBMED']
        csq = self.variant.INFO.get('CSQ')
        if csq is None: return
        csqSplit = csq.split("|")
        for i in range(len(csqSplit)):
            idx = i%len(idxs)
            key = idxs[idx]
        # print(self.variant.INFO.get('gnomad_popmax_af'))
        # print(self.variant)
        self.gnomad_popmax_af = float(self.variant.INFO.get('gnomad_popmax_af'))

    def getPathogenicSupportingCounts(self):
        return max(0, self.evidenceCodes["PP1"]) + max(0, self.evidenceCodes["PP2"]) + max(0, self.evidenceCodes["PP3"]) + max(0, self.evidenceCodes["PP4"]) + max(0, self.evidenceCodes["PP5"])

    def getPathogenicModerateCounts(self):
        return max(0, self.evidenceCodes["PM1"]) + max(0, self.evidenceCodes["PM2"]) + max(0, self.evidenceCodes["PM3"]) + max(0, self.evidenceCodes["PM4"]) + max(0, self.evidenceCodes["PM5"]) + max(0, self.evidenceCodes["PM6"])

    def getPathogenicStrongCounts(self):
        return max(0, self.evidenceCodes["PS1"]) + max(0, self.evidenceCodes["PS2"]) + max(0, self.evidenceCodes["PS3"]) + max(0, self.evidenceCodes["PS4"])

    def getPathogenicVeryStrongCounts(self):
        return max(0, self.evidenceCodes["PVS1"])

    def getBenignSupportingCounts(self):
        return max(0, self.evidenceCodes["BP1"]) + max(0, self.evidenceCodes["BP2"]) + max(0, self.evidenceCodes["BP3"]) + max(0, self.evidenceCodes["BP4"]) + max(0, self.evidenceCodes["BP5"]) + max(0, self.evidenceCodes["BP6"]) + max(0, self.evidenceCodes["BP7"])

    def getBenignModerateCounts(self):
        return 0

    def getBenignStrongCounts(self):
        return max(0, self.evidenceCodes["BS1"]) + max(0, self.evidenceCodes["BS2"]) + max(0, self.evidenceCodes["BS3"]) + max(0, self.evidenceCodes["BS4"])

    def getBenignVeryStrongCounts(self):
        return max(0, self.evidenceCodes["BA1"])
