using Distributions
mutable struct NodeConstructor
    num_connections
    num_source
    num_load
    num_LCL
    num_LC
    num_L
    num_fltr
    cntr
    tot_ele
    CM
    parameter
    S2S_p
    S2L_p
end

function NodeConstructor(;num_source, num_load, CM, parameter=nothing, S2S_p=0.1, S2L_p=0.8)

    tot_ele = num_source + num_load

    cntr = 0
    num_connections = 0

    

    if parameter === nothing

        #sample = 0.1 * num_source * random.normal(0,1)
        #num_LC = int(np.ceil(np.clip(sample, 1, num_source-1)))

        num_LC = 1 
        num_LCL = num_source - num_LC
        num_L = 0

        parameter = generate_parameter(num_LC, num_LCL, num_L)
    else

    end

    num_fltr = 4 * num_LCL + 2 * num_LC + 2 * num_L

    NodeConstructor(num_connections, num_source, num_load, num_LCL, num_LC, num_L, num_fltr
                cntr, tot_ele, CM, parameter, S2S_p, S2L_p)
end


function generate_parameter(num_LC, num_LCL, num_L)
    """Create parameter dict"""

        source_list = list()
        cable_list = list()
        load_list = list()

        for s in range(self.num_LCL):
            sample = self.sample_LCL_para()
            source_list.append(sample)
        
        for s in range(self.num_LC):
            sample = self.sample_LC_para()
            source_list.append(sample)
        
        for s in range(self.num_L):
            sample = self.sample_L_para()
            source_list.append(sample)

        for c in range(self.num_connections):
            sample = self.sample_cable_para()
            cable_list.append(sample)

        for l in range(self.num_load):
            sample = self.sample_load_para()
            load_list.append(sample)

        parameter = Dict()
        parameter['source'] = source_list
        parameter['cable'] = cable_list
        parameter['load'] = load_list
    
        return parameter
end


function cntr_fltr(source_list)
    cntr_LCL = 0
    cntr_LC = 0
    cntr_L = 0
    
    for _, source in enumerate(source_list):
        if source['fltr'] == 'LCL':
            cntr_LCL+=1
        elif source['fltr'] == 'LC':
            cntr_LC+=1
        elif source['fltr'] == 'L':
            cntr_L+=1

    return (cntr_LCL, cntr_LC, cntr_L)
end

function sample_LCL_para()

    #TODO randomize
    source = Dict()
    source["fltr"] = "LCL"
    source["R"] = 0.4
    source["L1"] = 2.3e-3
    source["L2"] = 2.3e-3
    source["C"] = 10e-6

    source
end

function sample_LC_para()
    """Sample source parameter"""      

    source = Dict()
    source["fltr"] = "LC"
    #source["R"] = np.round_(np.random.uniform(0.1, 1), 3)
    #source["L1"] = np.round_(np.random.uniform(2, 2.5), 3) * 1e-3
    #source["C"] = np.round_(np.random.uniform(5, 15), 3) * 1e-6

    #TODO
    source["R"] = 0.4
    source["L1"] = 2.3e-3
    source["C"] = 10e-6

    source
end

function sample_L_para()
    """Sample source parameter"""      

    source = Dict()
    source["fltr"] = "L"
    source["R"] = round(rand(Uniform(0.1, 1)), digits=3)
    source["L1"] = round(rand(Uniform(2, 2.5)), digits=3) * 1e-3

    source
end


function sample_load_para()
    """Sample load parameter"""

    load = Dict()
    load['R'] = round(rand(Uniform(10, 10000)), digits=3)

    #TODO
    load['R'] = 14

    load
end

function sample_cable_para()
    """Sample cable parameter"""

    l = rand(1:1:100)

    Rb = 0.722
    Cb = 8*10**-9
    Lb = 0.955*10**-3

    cable = Dict()
    cable['R'] = l * Rb
    cable['L'] = l * Lb
    cable['C'] = l * Cb

    #TODO
    # cable = dict()
    cable['R'] = 0.4
    cable['L'] = 2.3e-3
    cable['C'] = 1e-20

    cable
end


function tobe_or_n2b(self::NodeConstructor, x, p):
    """Sets x based on p to zero or to the value of the counter and increments it."""

    # To count up the connection, cntr is returned.
    # If only one type of cable is used this is not necessary an can be replaced by 1
    
    if x < p
        self.cntr += 1  
        return self.cntr
    else
        x = 0
        return x
    end
end

function generate_CM(self::NodeConstructor)
    """Constructs the CM

    Returns the constructed CM and the total number of connections.
    """

    # counting the connections 
    self.cntr = 0

    # get a upper triangular matrix
    mask = np.tri(self.tot_ele).T
    CM = np.random.rand(self.tot_ele,self.tot_ele) * mask # fill matrix with random entries between [0,1]
    CM = CM - np.eye(CM.shape[0]) * np.diag(CM) # delet diagonal bc no connection with itself

    # go through the matrix
    # -1 bc last entry is 0 anyway
    for i in range(self.tot_ele-1):

        # start at i, bc we need to check only upper triangle
        for j in range(i, self.tot_ele-1):
            if j >= self.num_source-1: # select propability according to column
                CM[i, j+1] = self.tobe_or_n2b(CM[i, j+1], self.S2L_p)
            else:
                CM[i, j+1] = self.tobe_or_n2b(CM[i, j+1], self.S2S_p)
            end
        end
    end

    # make sure that no objects disappear or subnets are formed
    for i in range(self.tot_ele):
        entries = list()
        
        # save rows and columns entries
        Col = CM[:i,i]
        Row = CM[i,i+1:]
        
        # get one list in the form of: [column, row]-entries
        entries.append(CM[:i,i].tolist())
        entries.append(CM[i,i+1:].tolist())
        entries = [item for sublist in entries for item in sublist]

        non_zero = np.sum([entries[i] != 0 for i in range(len(entries))]) # number of non_zero entries
        zero = np.sum([entries[i] == 0 for i in range(len(entries))]) # number of zero entries

        val_to_set = min(2, zero) # minimum of connections is 2
        
        if non_zero <= 2: # we need to set values if there are less then 2 entries
            idx_list = list() # create list to store indexes
            idx_row_entries = np.where(0==Col) # Get rows of the entries = 0
            idx_col_entries = np.where(0==Row) # Get col of the entries = 0

            idx_row_entries = idx_row_entries[0].tolist()
            idx_col_entries = idx_col_entries[0].tolist()

            idx_list.append([(j,i) for _,j in enumerate(idx_row_entries)]) 
            idx_list.append([(i,i+j+1) for _,j in enumerate(idx_col_entries)])
            idx_list = [item for sublist in idx_list for item in sublist]
            
            samples = np.array(val_to_set).clip(0, len(idx_list)) 
            idx_rnd = random.sample(range(0,len(idx_list)), samples) # draw samples from the list
            idx_rnd = np.array(idx_rnd) 
            
            for _, ix in enumerate(idx_rnd):
                # Based on the random sample, select an indize
                # from the list and write into the corresponding CM cell.
                CM[idx_list[ix]] = self.count_up() 
            end
        end
    end

    
    CM = CM - CM.T # copy with negative sign to lower triangle

    # save CM
    self.CM = CM

    # save number of connections
    self.num_connections = self.cntr

end


function get_A_source(self::NodeConstructor, source_i):
    """Create the A_source entry for a source in the A matrix

    Returns:
        A_source: Matrix with values belonging to corresponding source (2, 2)
    """
    parameter_i = self.source[source_i-1]

    if parameter_i['fltr'] == 'LCL':

        A_source = np.zeros((4,4))
        A_source[0,0] = -parameter_i['R']/parameter_i['L1']
        A_source[0,1] = -1/parameter_i['L1']
        A_source[1,0] = 1/parameter_i['C']
        A_source[1,2] = -1/parameter_i['C']
        A_source[2,1] = 1/parameter_i['L2']
        A_source[2,3] = -1/parameter_i['L2']
        
        C_sum =  0
        
        CM_row = self.CM[source_i-1]
        
        indizes = list(CM_row[CM_row != 0])
        signs = np.sign(indizes) # get signs
        indizes_ = indizes*signs # delet signs from indices
        indizes_.astype(dtype=np.int32)
        
        for _, idx in enumerate(indizes_):
            idx = int(idx)
            C_sum += self.parameter['cable'][idx-1]['C']
        end
        
        A_source[3,2] = C_sum**-1

    elseif parameter_i['fltr'] == 'LC':

        A_source = np.zeros((2,2))
        A_source[0,0] = -parameter_i['R']/parameter_i['L1']
        A_source[0,1] = -1/parameter_i['L1']
        
        C_sum =  parameter_i['C']
        
        CM_row = self.CM[source_i-1]
        
        indizes = list(CM_row[CM_row != 0])
        signs = np.sign(indizes) # get signs
        indizes_ = indizes*signs # delet signs from indices
        
        for _, idx in enumerate(indizes_):
            idx = int(idx)
            C_sum += self.parameter['cable'][idx-1]['C']
        end
        
        A_source[1,0] = C_sum**-1

    elseif parameter_i['fltr'] == 'L':
        raise NotImplementedError

    else:
        raise f"Expect filter to be 'LCL', 'LC' or 'L', not {parameter_i['fltr']}."
    end

    return A_source

end

function get_B_source(self::NodeConstructor, source_i):
    """Create the B_source entry for a source in the B matrix

    Return:
        B_source: Matrix with values belonging to corresponding source (2, 1)
    """
    parameter_i = self.source[source_i-1]

    if parameter_i['fltr'] == 'LCL':

        B_source = np.zeros((4,1))
        B_source[0,0] =  1/parameter_i['L1']

    elseif parameter_i['fltr'] == 'LC':

        B_source = np.zeros((2,1))
        B_source[0,0] =  1/parameter_i['L1']

    elseif parameter_i['fltr'] == 'L':
        raise NotImplementedError
    end

    return B_source
end

function get_A_col(self::NodeConstructor, source_i):
    """Create the A_col entry in the A matrix
    Return:
        A_col: Matrix with the column entries for A (2, num_connections)
    """

    parameter_i = self.source[source_i-1]

    if parameter_i['fltr'] == 'LCL':

        A_col = np.zeros((4, self.num_connections))

        CM_row = self.CM[source_i-1]

        indizes = list(CM_row[CM_row != 0]) # get entries unequal 0
        signs = np.sign(indizes) # get signs
        indizes_ = indizes*signs # delet signs from indices
        indizes_.astype(dtype=np.int32)

        C_sum = 0 

        for _, (idx, sign) in enumerate(zip(indizes_, signs)):
            idx = int(idx)
            C_sum += self.parameter['cable'][idx-1]['C']

            A_col[3,idx-1] = sign * -(C_sum**-1)
        end

    elseif parameter_i['fltr'] == 'LC':

        A_col = np.zeros((2, self.num_connections))

        CM_row = self.CM[source_i-1]

        indizes = list(CM_row[CM_row != 0]) # get entries unequal 0
        signs = np.sign(indizes) # get signs
        indizes_ = indizes*signs # delet signs from indices
        indizes_.astype(dtype=np.int32)

        C_sum = parameter_i['C']

        for _, (idx, sign) in enumerate(zip(indizes_, signs)):
            idx = int(idx)
            C_sum += self.parameter['cable'][idx-1]['C']

            A_col[1,idx-1] = sign * -(C_sum**-1)
        end

    elseif parameter_i['fltr'] == 'L':
        raise NotImplementedError
    end

    return A_col
end

function get_A_row(self::NodeConstructor, source_i):
    """Create the A_row entry in the A matrix
    Return:
        A_row: Matrix with the row entries for A (num_connections, 2)
    """
    parameter_i = self.source[source_i-1]

    if parameter_i['fltr'] == 'LCL':

        A_row = np.zeros((4, self.num_connections))
        CM_col = self.CM[source_i-1]
        
        indizes = list(CM_col[CM_col != 0]) # get entries unequal 0
        signs = np.sign(indizes) # get signs
        indizes_ = indizes*signs # delet signs from indices
        indizes_.astype(dtype=np.int32)
        
        for _, (idx, sign) in enumerate(zip(indizes_, signs)):
            idx = int(idx)
            A_row[3,idx-1] = sign * 1/self.parameter['cable'][idx-1]['L']
        end

    elseif parameter_i['fltr'] == 'LC':

        A_row = np.zeros((2, self.num_connections))
        
        CM_col = self.CM[source_i-1]
        
        indizes = list(CM_col[CM_col != 0]) # get entries unequal 0
        signs = np.sign(indizes) # get signs
        indizes_ = indizes*signs # delet signs from indices
        
        for _, (idx, sign) in enumerate(zip(indizes_, signs)):
            idx = int(idx)
            A_row[1,idx-1] = sign * 1/self.parameter['cable'][idx-1]['L']
        end

    elseif parameter_i['fltr'] == 'L':
        raise NotImplementedError
    end

    return A_row.T
end

function generate_A_tran_diag(self::NodeConstructor):
    """Create A_tran_diag"""

    diag = np.eye(self.num_connections)
    vec = np.zeros(self.num_connections)[:, None]
    for i, ele in enumerate(self.parameter['cable']):
        vec[i] = -ele['R']/ele['L']
    end
    A_tran_diag = vec*diag

    return A_tran_diag
end

function generate_A_load_col(self::NodeConstructor, load_i):
        
    A_load_col = np.zeros(self.num_connections)

    CM_row = self.CM[(self.num_source-1)+load_i]

    indizes = list(CM_row[CM_row != 0]) # get entries unequal 0
    signs = np.sign(indizes) # get signs

    indizes_ = indizes*signs # delet signs from indices
    indizes_.astype(dtype=np.int32)

    for _, (idx, sign) in enumerate(zip(indizes_, signs)):
        idx = int(idx)
        C_sum = 0

        for j, ele in enumerate(self.parameter['cable']):
            C_sum += ele['C']
        end
    end

        A_load_col[idx-1] = sign * -(C_sum**-1)
    return A_load_col
end


function generate_A_load_row(self::NodeConstructor, load_i):
            
    A_load_row = np.zeros(self.num_connections)

    CM_col = self.CM[(self.num_source-1)+load_i]

    indizes = list(CM_col[CM_col != 0]) # get entries unequal 0

    signs = np.sign(indizes) # get signs
    indizes_ = indizes*signs # delet signs from indices

    for i, (idx, sign) in enumerate(zip(indizes_, signs)):
        idx = int(idx)

        A_load_row[idx-1] = sign *1/self.parameter['cable'][idx-1]['L'] 
    end 

    return A_load_row
end


function generate_A_load_diag(self::NodeConstructor):
    diag = np.eye(self.num_load)
    vec = np.zeros(self.num_load)

    for i, ele in enumerate(self.parameter['load']):
        CM_row = self.CM[(self.num_source)+i]
        indizes = list(CM_row[CM_row != 0])
        signs = np.sign(indizes) # get signs
        indizes_ = indizes*signs # delet signs from indices
        C_sum = 0
        for _, idx in enumerate(indizes_):
            idx = int(idx)
            
            C_sum += self.parameter['cable'][idx-1]['C']  # Cb[idx]
        end

        vec[i] = - (ele['R'] * (C_sum))**-1 # Rload[i]
    end

    A_load_diag = vec*diag

    return A_load_diag
end


function generate_A(self::NodeConstructor):
    """Generate the A matrix

    The previously constructed matrices are now plugged together in the form:
        [[A_source, A_col,       0          ],
        [A_row,    A_tran_diag, A_load_row ],
        [0,        A_load_col,  A_load_diag]]
    with A_source:
        [[LCL, 0 , 0]
        [0,   LC, 0]
        [0,   0,  L]]
    Returns:
        A: A matrix for state space ((2*num_source+num_connections),(2*num_source+num_connections))
    """
    # get A_source
    self.num_fltr = 4*self.num_LCL + 2*self.num_LC + 2*self.num_L
    A_source = np.zeros((self.num_fltr, self.num_fltr)) # construct matrix of zeros
    A_source_list = [self.get_A_source(i) for i in range(1,self.num_source+1)]
            
    for i, ele in enumerate(A_source_list):
        if i < self.num_LCL:
            start = 4*i
            stop = 4*i+4
            A_source[start:stop,start:stop] = ele

        elseif i < self.num_LCL+self.num_LC:
            start = 2*i + 2*self.num_LCL
            stop = 2*i+2 + 2*self.num_LCL
            A_source[start:stop,start:stop] = ele

        elseif i < self.num_LCL+self.num_LC+self.num_L:
            start = 2*i + 2*self.num_LCL 
            stop = 2*i+2 + 2*self.num_LCL
            A_source[start:stop,start:stop] = ele
        end
    end


    # get A_col
    A_col = np.zeros((self.num_fltr, self.num_connections))
    A_col_list = [self.get_A_col(i) for i in range(1,self.num_source+1)] # start at 1 bc Source 1 ...

    for i, ele in enumerate(A_col_list):
        if i < self.num_LCL:
            start = 4*i
            stop = 4*i+4
            A_col[start:stop,:] = ele

        elseif i < self.num_LCL+self.num_LC:
            start = 2*i + 2*self.num_LCL
            stop = 2*i+2 + 2*self.num_LCL
            A_col[start:stop,:] = ele

        elseif i < self.num_LCL+self.num_LC+self.num_L:
            start = 2*i + 2*self.num_LCL 
            stop = 2*i+2 + 2*self.num_LCL
            A_col[start:stop,:] = ele
        end
    end

    # get A_row
    A_row = np.zeros((self.num_connections, self.num_fltr))
    A_row_list = [self.get_A_row(i) for i in range(1,self.num_source+1)] # start at 1 bc Source 1 ...

    for i, ele in enumerate(A_row_list):
        if i < self.num_LCL:
            start = 4*i
            stop = 4*i+4
            A_row[:,start:stop] = ele

        elseif i < self.num_LCL+self.num_LC:
            start = 2*i + 2*self.num_LCL
            stop = 2*i+2 + 2*self.num_LCL
            A_row[:,start:stop] = ele

        elseif i < self.num_LCL+self.num_LC+self.num_L:
            start = 2*i + 2*self.num_LCL 
            stop = 2*i+2 + 2*self.num_LCL
            A_row[:,start:stop] = ele
        end
    end

    A_tran_diag = self.generate_A_tran_diag()

    A_load_row_list = list()
    for i in range(self.num_load):
        A_load_row_list.append(self.generate_A_load_row(i+1))
    end
    A_load_row = np.vstack(A_load_row_list).transpose() # i-> idx // i+1 -> num of load

    A_load_col_list = list()
    for i in range(self.num_load):
        A_load_col_list.append(self.generate_A_load_col(i+1))
    end
    A_load_col = np.vstack(A_load_col_list)

    A_load_diag = self.generate_A_load_diag()

    #         A_transition = np.block([A_tran_diag, A_load_col],
    #                                 [A_load_col, A_load_diag])

    A_load_zeros = np.zeros((self.num_fltr, self.num_load))

    A_load_zeros_t = A_load_zeros.transpose()

    A = np.block([[A_source, A_col, A_load_zeros],
                [A_row, A_tran_diag, A_load_row],
                [A_load_zeros_t, A_load_col, A_load_diag]])

    return A
end



function generate_B(self::NodeConstructor):
    """Generate the B matrix

    The previously constructed matrices are now plugged together in the form:
        [[B_source,        0, ...,         0],
        [       0, B_source, ...,         0],
        [       0,        0, ...,         0],
        [       0,        0, ...,  B_source]]
    Returns:
        B: B matrix for state space (2*num_source+num_connections,num_source)
    """
    B = np.zeros((self.num_fltr + self.num_connections + self.num_load,self.num_source))

    B_source_list = [self.get_B_source(i) for i in range(1,self.num_source+1)] # start at 1 bc Source 1 ...

    for i, ele in enumerate(B_source_list):
        if i < self.num_LCL:
            start = 4*i
            stop = 4*i+4
            B[start:stop,i:i+1] = ele

        elseif i < self.num_LCL+self.num_LC:
            start = 2*i + 2*self.num_LCL
            stop = 2*i+2 + 2*self.num_LCL
            B[start:stop,i:i+1] = ele

        elseif i < self.num_LCL+self.num_LC+self.num_L:
            start = 2*i
            stop = 2*i+2
            B[start:stop,i:i+1] = ele
        end
    end

    return B
end



function generate_C(self::NodeConstructor):
    """Generate the C matrix

    Retruns:
        C: Identity matrix (2*num_source+num_connections)
    """
    return np.eye(self.num_fltr + self.num_connections + self.num_load)
end

function generate_D(self::NodeConstructor):
    """Generate the D vector

    Retruns:
        0: Zero vector (2*num_source+num_connections)
    """
    return 0
end

function get_sys(self::NodeConstructor):
    """Returns state space matrices"""

    A = self.generate_A()
    B = self.generate_B()
    C = self.generate_C()
    D = self.generate_D()
    return (A, B, C, D)
end


function get_states(self::NodeConstructor):
    states = list()
    for s in range(1, self.num_source+1):
        if s < self.num_LCL:
            states.append("i_f$s")    # i_f1; dann i_f2....
            states.append("u_f$s")
            states.append("i_$s")
            states.append("u_$s")

        elseif s < self.num_LCL+self.num_LC+self.num_L:
            states.append("i_$s")
            states.append("u_$s")
        end

    for c in range(1, self.num_connections+1):
        states.append("i_c$c")
    end

    for l in range(1, self.num_load+1):
        states.append("u_l$l")
    end
    return states
end

function draw_graph(self::NodeConstructor):
    """Plots a graph according to the CM matrix

    Red nodes corresponse to a source.
    Lightblue nodes corresponse to a load.
    """

    edges = []
    color = []
    for i in range(1, self.num_connections+1):
        (row, col) = np.where(self.CM==i)
        (row_idx, col_idx) = (row[0]+1, col[0]+1)
        edges.append((row_idx, col_idx))
        if row_idx <= self.num_source:
            color.append('red')
        else:
            color.append('blue')
        end
    end

    G = nx.Graph(edges)

    color_map = []

    for node in G:
        if node <= self.num_source:
            color_map.append("red")
        else:
            color_map.append("lightblue")
        end
    end

    nx.draw(G, node_color=color_map, with_labels = True)
    plt.show()

    pass
end
