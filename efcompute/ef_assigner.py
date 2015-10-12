import sys
import fractions
from math import ceil,floor
from golden_rules import golden_rules

infinite = sys.maxint

atom_masses = {'C':12.00000000000,
                'H':1.00782503214,
                'N':14.00307400524,
                'O':15.99491462210,
                'P':30.97376151200,
                'S':31.97207069000}

proton_mass = 1.00727645199076

class ef_assigner(object):
	def __init__(self,atoms = ['C','H','N','O','P','S'],scale_factor=1000,enforce_ppm = True,do_7_rules = True):
		self.atoms = atoms
		self.scale_factor = scale_factor
		self.a = self.get_dictionary()
		self.rr = self.round_robin()
		self.enforce_ppm = enforce_ppm
		self.do_7_rules = do_7_rules
		# Compute correction factor for upper bound
		self.delta = 0
		for i in atoms:
		    delta_i = (ceil(scale_factor*atom_masses[i]) - scale_factor*atom_masses[i])/atom_masses[i]
		    if delta_i > self.delta:
				self.delta = delta_i
		print self.delta

	def find_all(self,mass,i,c,ppm,precursor_mass):
	    if i == 0:
	        c[0] = mass/self.a[0]
	        # The following corrects for the fact that at low scale factors we
	        # will find things at much more than the specificed ppm
	        if self.enforce_ppm:
	        	molecule_mass = 0.0
	        	for i,atom in enumerate(self.atoms):
	        		molecule_mass += atom_masses[atom]*c[i]
        		if abs(molecule_mass - precursor_mass)/precursor_mass <= 1e-6*ppm:
        			formulas.append(list(c))

        		return
	        else:
	        	formulas.append(list(c))
	        return
	    else:
	        lcm = self.a[0]*self.a[i] / fractions.gcd(self.a[0],self.a[i])
	        l = lcm/self.a[i]
	        for j in range(0,l):
	            c[i] = j
	            m = mass - j*self.a[i]
	            r = m % self.a[0]
	            lbound = self.rr[i-1][r]
	            while m >= lbound:
	                self.find_all(m,i-1,c,ppm,precursor_mass)
	                m = m - lcm
	                c[i] = c[i] + l


	def find_formulas(self,precursor_mass_list,ppm = 5,polarisation="None"):
		global formulas
		print "Finding formulas at {}ppm".format(ppm)
		formulas_out = {}
		gr = golden_rules()
		top_hit_string = []
		for precursor_mass in precursor_mass_list:

		    float_mass = float(precursor_mass)
		    k = len(self.rr)
		    c = [0 for i in range(0, k)]

		    print "Searching for {}".format(float_mass)
		    formulas = []

		    if polarisation == "POS":
		    	float_mass -= proton_mass
		    elif polarisation == "NEG":
		    	float_mass += proton_mass
		    	
		    ppm_error = ppm*float_mass/1e6
		    lower_bound = float_mass - ppm_error
		    upper_bound = float_mass + ppm_error


		    int_lower_bound = int(ceil(lower_bound*self.scale_factor))
		    int_upper_bound = int(floor(upper_bound*self.scale_factor + self.delta*upper_bound))

		    for int_mass in range(int_lower_bound,int_upper_bound+1):
		        self.find_all(int_mass,k-1,c,ppm,float_mass)

		    print "\t found {}".format(len(formulas))

		    formulas_out[precursor_mass] = []
		    for f in formulas:
		    	formula = {}
		    	for i,a in enumerate(self.atoms):
		    		formula[a] = f[i]
		    	formulas_out[precursor_mass].append(formula)

		    if self.do_7_rules:
		    	filtered_formulas_out = {}
		    	filtered_formulas_out[precursor_mass],passed,failed = gr.filter_list(formulas_out[precursor_mass])
		    	formulas_out[precursor_mass] = filtered_formulas_out[precursor_mass]
		    
		    if polarisation == "POS":
		    	for f in formulas_out[precursor_mass]:
		    		f['H'] += 1
		    elif polarisation == "NEG":
		    	for f in formulas_out[precursor_mass]:
		    		f['H'] -= 1

		    # If there is more than one hit return the top hit as a top_hit_string
		    if len(formulas_out[precursor_mass]) == 0:
		    	top_hit_string.append(None)
		    	continue
		    else:
		    	closest = None
		    	for f in formulas_out[precursor_mass]:
		    		mass = 0.0
		    		f_string = ""
		    		for atom in f:
		    			mass += f[atom]*atom_masses[atom]
		    			if f[atom]>1:
		    				f_string += "{}{}".format(atom,f[atom])
		    			elif f[atom] == 1:
		    				f_string += "{}".format(atom)
		    		er = abs(mass - float_mass)
		    		if closest == None:
		    			best_er = er
		    			closest = f_string
	    			elif best_er < er:
	    				closest = f_string
	    		top_hit_string.append(f_string)


		return formulas_out,top_hit_string


	def get_dictionary(self):
	    atom_dict = []
	    for a in self.atoms:
	        atom_dict.append(int(ceil(atom_masses[a]*self.scale_factor)))
	    return atom_dict


	def find_n(self,n, p, d):
	    minimum = infinite
	    for q, elem in enumerate(n):
	        if q % d == p:
	            if elem < minimum:
	                minimum = elem
	    return minimum


	def round_robin(self):
    
	    k = len(self.a)
	    a1 = self.a[0]
	    n = [infinite for r in range(0, a1)]
	    n[0] = 0
	    

	    rr = []
	    rr.append(list(n))
	    

	    for i in range(1, k):
	        d = fractions.gcd(a1, self.a[i])
	        for p in range(0, d):
	            new_n = self.find_n(n, p, d)
	            if new_n < infinite:
	                for repeat in range(1, a1/d):
	                    new_n = new_n + self.a[i]
	                    r = new_n % a1
	                    new_n = min(new_n, n[r])
	                    n[r] = new_n
	        
	        rr.append(list(n))

	    return rr


