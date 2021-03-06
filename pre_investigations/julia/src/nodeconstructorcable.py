import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import random


class NodeConstructorCable():
    """Node Constructor implementation with cable modeling.
    Helper class for creating a grid structure for scaling purposes. The grid can be defined externally via a so-called CM matrix or randomly generated by the class. The given grid structure is then used to create the ODE equation systems. The output of the equation systems is done via the state space representation with the help of the A, B, C and D matrices. The generated grid can be visualized additionally.
    Attributes:
        num_source: Number of sources in the grid (1,)
        num_loads: Number of loads in the grid (1,)
        tot_ele: Total number of objects in the grid (1,)
        
        parameter: Dict which includes the parameters of the components 
        S2S_p: Probability that a source is connected to a source (1,)
        S2L_p: Probability that a source is connected to a load (1,)
        num_connections: Number of drawn connections between all objects (1,)
        CM: Connection Matrix specifies which objects are linked to each other via which connection (tot_ele, tot_ele)
        generate_CM: Function that generates CM randomly. A connection to the network is guaranteed, so that no subnets can occur.
        get_sys: Function which outputs the system matrices in the statespace representation
        get_states: Function which returns a list of strings with all states for the given system
        draw_graph: Function which plots a graph based on the CM
    """

    def __init__(self, num_source, num_load, CM=None, parameter=None, S2S_p=0.1, S2L_p=0.8):
        """Creates and initialize a nodeconstructor class instance.
        First the parameters are unpacked and then a CM is created, if not passed.
        Args:
            num_source: Number of sources in the grid (1,)
            num_loads: Number of loads in the grid (1,)
            parameter: Dict which includes the parameters of the components
            S2S_p: Probability that a source is connected to a source (1,)
            S2L_p: Probability that a source is connected to a load (1,)
            CM: Connection Matrix specifies which objects are linked to each other via which connection (tot_ele, tot_ele)
        
        """
        self.num_source = num_source
        self.num_load = num_load
        self.tot_ele = num_source + num_load

        self.S2S_p = S2S_p
        self.S2L_p = S2L_p
        self.cntr = 0
        self.num_connections = 0

        # check CM
        if isinstance(CM, np.ndarray):
            assert self.tot_ele == CM.shape[0], (
                f"Expect the number of elements in the node to match the specified structure in the CM, but got {self.tot_ele} and {CM.shape[0]}")
            self.CM = CM
            self.num_connections = int(np.amax(CM))
        elif CM == None:
            self.generate_CM()
        else:
            raise f"Expect CM to be an np.ndarray or None, not {type(CM)}."

        # unpack parameters
        if isinstance(parameter, dict):
            assert len(list(
                parameter.keys())) == 3, f"Expect parameter to have three entries but got {len(list(parameter.keys()))}"

            assert sorted(list(parameter.keys())) == sorted(['cable', 'source', 'load']), (
                f"Expect parameter to have the three entries 'cable', 'load' and 'source' but got {sorted(list(parameter.keys()))}.")

            self.parameter = parameter

            assert self.num_source == len(self.parameter['source']), (
                f"Expect the number of sources to match the number of sources in the parameters, but got {self.num_source} and {len(self.parameter['source'])}.")

            assert self.num_load == len(self.parameter['load']), (
                f"Expect the number of loads to match the number of loads in the parameters, but got {self.num_load} and {len(self.parameter['load'])}.")

            assert self.num_connections == len(self.parameter['cable']), (
                f"Expect the number of connections to match the number of cables in the parameters, but got {self.num_connections} and {len(self.parameter['cable'])}.")

            self.num_LCL, self.num_LC, self.num_L = self.cntr_fltr(self.parameter['source'])

            assert self.num_source == (self.num_LCL + self.num_LC + self.num_L), (
                f"Expect the number of sources to be identical to the sum of the filter types, but the number of sources is {self.num_source} and the sum of the filters is {(self.num_LCL + self.num_LC + self.num_L)} .")

        elif parameter == None:
            self.parameter = self.generate_parameter()

        else:
            raise f"Expect parameter to be an dict or None, not {type(parameter)}."

        self.source = self.parameter['source']
        self.cable = self.parameter['cable']
        self.load = self.parameter['load']

    def generate_parameter(self):
        """Create parameter dict"""

        source_list = list()
        cable_list = list()
        load_list = list()

        self.get_filter_distribution()

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

        parameter = dict()
        parameter['source'] = source_list
        parameter['cable'] = cable_list
        parameter['load'] = load_list

        return parameter

    def get_filter_distribution(self):

        sample = 0.1 * self.num_source * np.random.normal(0, 1)
        # self.num_LC = int(np.ceil(np.clip(sample, 1, self.num_source-1)))
        self.num_LC = 1

        self.num_LCL = self.num_source - self.num_LC
        # self.num_LCL = 0
        self.num_L = 0
        pass

    def cntr_fltr(self, source_list):

        cntr_LCL = 0
        cntr_LC = 0
        cntr_L = 0

        for _, source in enumerate(source_list):
            if source['fltr'] == 'LCL':
                cntr_LCL += 1
            elif source['fltr'] == 'LC':
                cntr_LC += 1
            elif source['fltr'] == 'L':
                cntr_L += 1

        return (cntr_LCL, cntr_LC, cntr_L)

    def sample_LCL_para(self):
        """Sample source parameter"""

        source = dict()
        source['fltr'] = 'LCL'
        # source['R'] = np.round_(np.random.uniform(0.1, 1), 3)
        # source['L1'] = np.round_(np.random.uniform(2, 2.5), 3) * 1e-3
        # source['L2'] = np.round_(np.random.uniform(2, 2.5), 3) * 1e-3
        # source['C'] = np.round_(np.random.uniform(5, 15), 3) * 1e-6

        source['R'] = 0.4
        source['L1'] = 2.3e-3
        source['L2'] = 2.3e-3
        source['C'] = 10e-6

        # source['R'] = 10
        # source['L1'] = 5
        # source['L2'] = 5
        # source['C'] = 2

        return source

    def sample_LC_para(self):
        """Sample source parameter"""

        source = dict()
        source['fltr'] = 'LC'
        # source['R'] = np.round_(np.random.uniform(0.1, 1), 3)
        # source['L1'] = np.round_(np.random.uniform(2, 2.5), 3) * 1e-3
        # source['C'] = np.round_(np.random.uniform(5, 15), 3) * 1e-6

        source['R'] = 0.4
        source['L1'] = 2.3e-3
        source['C'] = 10e-6

        # source['R'] = 10
        # source['L1'] = 5
        # source['C'] = 2

        return source

    def sample_L_para(self):
        """Sample source parameter"""

        source = dict()
        source['fltr'] = 'L'
        source['R'] = np.round_(np.random.uniform(0.1, 1), 3)
        source['L1'] = np.round_(np.random.uniform(2, 2.5), 3) * 1e-3

        return source

    def sample_load_para(self):
        """Sample load parameter"""

        load = dict()
        # load['R'] = np.round_(np.random.uniform(10, 10000), 3)
        load['R'] = 14

        return load

    def sample_cable_para(self):
        """Sample cable parameter"""

        l = np.random.randint(1, 100)
        l = 50

        Rb = 0.722
        Cb = 8 * 10 ** -9  # too small?
        Lb = 0.955 * 10 ** -3

        # Rb = 10
        # Cb = 2
        # Lb = 5

        cable = dict()
        cable['R'] = l * Rb
        cable['L'] = l * Lb
        cable['C'] = l * Cb

        #cable["R"] = 0.4
        #cable["L"] = 2.3e-3
        #cable["C"] = 1e-20

        return cable

    def tobe_or_n2b(self, x, p):
        """Sets x based on p to zero or to the value of the counter and increments it."""

        # To count up the connection, cntr is returned.
        # If only one type of cable is used this is not necessary an can be replaced by 1

        if x < p:
            self.cntr += 1
            return self.cntr
        else:
            x = 0
            return x

    def count_up(self):
        """Increment counter"""

        self.cntr += 1
        return self.cntr

    def generate_CM(self):
        """Constructs the CM
        
        Returns the constructed CM and the total number of connections.
        """

        # counting the connections 
        self.cntr = 0

        # get a upper triangular matrix
        mask = np.tri(self.tot_ele).T
        CM = np.random.rand(self.tot_ele, self.tot_ele) * mask  # fill matrix with random entries between [0,1]
        CM = CM - np.eye(CM.shape[0]) * np.diag(CM)  # delet diagonal bc no connection with itself

        # go through the matrix
        # -1 bc last entry is 0 anyway
        for i in range(self.tot_ele - 1):

            # start at i, bc we need to check only upper triangle
            for j in range(i, self.tot_ele - 1):
                if j >= self.num_source - 1:  # select propability according to column
                    CM[i, j + 1] = self.tobe_or_n2b(CM[i, j + 1], self.S2L_p)
                else:
                    CM[i, j + 1] = self.tobe_or_n2b(CM[i, j + 1], self.S2S_p)

        # make sure that no objects disappear or subnets are formed
        for i in range(self.tot_ele):
            entries = list()

            # save rows and columns entries
            Col = CM[:i, i]
            Row = CM[i, i + 1:]

            # get one list in the form of: [column, row]-entries
            entries.append(CM[:i, i].tolist())
            entries.append(CM[i, i + 1:].tolist())
            entries = [item for sublist in entries for item in sublist]

            non_zero = np.sum([entries[i] != 0 for i in range(len(entries))])  # number of non_zero entries
            zero = np.sum([entries[i] == 0 for i in range(len(entries))])  # number of zero entries

            val_to_set = min(2, zero)  # minimum of connections is 2

            if non_zero <= 2:  # we need to set values if there are less then 2 entries
                idx_list = list()  # create list to store indexes
                idx_row_entries = np.where(0 == Col)  # Get rows of the entries = 0
                idx_col_entries = np.where(0 == Row)  # Get col of the entries = 0

                idx_row_entries = idx_row_entries[0].tolist()
                idx_col_entries = idx_col_entries[0].tolist()

                idx_list.append([(j, i) for _, j in enumerate(idx_row_entries)])
                idx_list.append([(i, i + j + 1) for _, j in enumerate(idx_col_entries)])
                idx_list = [item for sublist in idx_list for item in sublist]

                samples = np.array(val_to_set).clip(0, len(idx_list))
                idx_rnd = random.sample(range(0, len(idx_list)), samples)  # draw samples from the list
                idx_rnd = np.array(idx_rnd)

                for _, ix in enumerate(idx_rnd):
                    # Based on the random sample, select an indize
                    # from the list and write into the corresponding CM cell.
                    CM[idx_list[ix]] = self.count_up()

        CM = CM - CM.T  # copy with negative sign to lower triangle

        # save CM
        self.CM = CM

        # save number of connections
        self.num_connections = self.cntr
        pass

    def get_A_source(self, source_i):
        """Create the A_source entry for a source in the A matrix
        
        Returns:
            A_source: Matrix with values belonging to corresponding source (2, 2)
        """
        parameter_i = self.source[source_i - 1]

        if parameter_i['fltr'] == 'LCL':

            A_source = np.zeros((4, 4))
            A_source[0, 0] = -parameter_i['R'] / parameter_i['L1']
            A_source[0, 1] = -1 / parameter_i['L1']
            A_source[1, 0] = 1 / parameter_i['C']
            A_source[1, 2] = -1 / parameter_i['C']
            A_source[2, 1] = 1 / parameter_i['L2']
            A_source[2, 3] = -1 / parameter_i['L2']

            C_sum = 0

            CM_row = self.CM[source_i - 1]

            indizes = list(CM_row[CM_row != 0])
            signs = np.sign(indizes)  # get signs
            indizes_ = indizes * signs  # delet signs from indices
            indizes_.astype(dtype=np.int32)

            for _, idx in enumerate(indizes_):
                idx = int(idx)
                C_sum += self.parameter['cable'][idx - 1]['C']

            A_source[3, 2] = C_sum ** -1

        elif parameter_i['fltr'] == 'LC':

            A_source = np.zeros((2, 2))
            A_source[0, 0] = -parameter_i['R'] / parameter_i['L1']
            A_source[0, 1] = -1 / parameter_i['L1']

            C_sum = parameter_i['C']

            CM_row = self.CM[source_i - 1]

            indizes = list(CM_row[CM_row != 0])
            signs = np.sign(indizes)  # get signs
            indizes_ = indizes * signs  # delet signs from indices

            for _, idx in enumerate(indizes_):
                idx = int(idx)
                C_sum += self.parameter['cable'][idx - 1]['C']

            A_source[1, 0] = C_sum ** -1

        elif parameter_i['fltr'] == 'L':
            raise NotImplementedError

        else:
            raise f"Expect filter to be 'LCL', 'LC' or 'L', not {parameter_i['fltr']}."

        return A_source

    def get_B_source(self, source_i):
        """Create the B_source entry for a source in the B matrix
        
        Return:
            B_source: Matrix with values belonging to corresponding source (2, 1)
        """
        parameter_i = self.source[source_i - 1]

        if parameter_i['fltr'] == 'LCL':

            B_source = np.zeros((4, 1))
            B_source[0, 0] = 1 / parameter_i['L1']

        elif parameter_i['fltr'] == 'LC':

            B_source = np.zeros((2, 1))
            B_source[0, 0] = 1 / parameter_i['L1']

        elif parameter_i['fltr'] == 'L':
            raise NotImplementedError

        return B_source

    def get_A_col(self, source_i):
        """Create the A_col entry in the A matrix
        Return:
            A_col: Matrix with the column entries for A (2, num_connections)
        """

        parameter_i = self.source[source_i - 1]

        if parameter_i['fltr'] == 'LCL':

            A_col = np.zeros((4, self.num_connections))

            CM_row = self.CM[source_i - 1]

            indizes = list(CM_row[CM_row != 0])  # get entries unequal 0
            signs = np.sign(indizes)  # get signs
            indizes_ = indizes * signs  # delet signs from indices
            indizes_.astype(dtype=np.int32)

            C_sum = 0

            for _, (idx, sign) in enumerate(zip(indizes_, signs)):
                idx = int(idx)
                C_sum += self.parameter['cable'][idx - 1]['C']

            for _, (idx, sign) in enumerate(zip(indizes_, signs)):
                idx = int(idx)
                A_col[3, idx - 1] = sign * -(C_sum ** -1)


        elif parameter_i['fltr'] == 'LC':

            A_col = np.zeros((2, self.num_connections))

            CM_row = self.CM[source_i - 1]

            indizes = list(CM_row[CM_row != 0])  # get entries unequal 0
            signs = np.sign(indizes)  # get signs
            indizes_ = indizes * signs  # delet signs from indices
            indizes_.astype(dtype=np.int32)

            C_sum = parameter_i['C']

            for _, (idx, sign) in enumerate(zip(indizes_, signs)):
                idx = int(idx)
                C_sum += self.parameter['cable'][idx - 1]['C']

            for _, (idx, sign) in enumerate(zip(indizes_, signs)):
                idx = int(idx)
                A_col[1, idx - 1] = sign * -(C_sum ** -1)

        elif parameter_i['fltr'] == 'L':
            raise NotImplementedError

        return A_col

    def get_A_row(self, source_i):
        """Create the A_row entry in the A matrix
        Return:
            A_row: Matrix with the row entries for A (num_connections, 2)
        """
        parameter_i = self.source[source_i - 1]

        if parameter_i['fltr'] == 'LCL':

            A_row = np.zeros((4, self.num_connections))
            CM_col = self.CM[source_i - 1]

            indizes = list(CM_col[CM_col != 0])  # get entries unequal 0
            signs = np.sign(indizes)  # get signs
            indizes_ = indizes * signs  # delet signs from indices
            indizes_.astype(dtype=np.int32)

            for _, (idx, sign) in enumerate(zip(indizes_, signs)):
                idx = int(idx)
                A_row[3, idx - 1] = sign * 1 / self.parameter['cable'][idx - 1]['L']

        elif parameter_i['fltr'] == 'LC':

            A_row = np.zeros((2, self.num_connections))

            CM_col = self.CM[source_i - 1]

            indizes = list(CM_col[CM_col != 0])  # get entries unequal 0
            signs = np.sign(indizes)  # get signs
            indizes_ = indizes * signs  # delet signs from indices

            for _, (idx, sign) in enumerate(zip(indizes_, signs)):
                idx = int(idx)
                A_row[1, idx - 1] = sign * 1 / self.parameter['cable'][idx - 1]['L']

        elif parameter_i['fltr'] == 'L':
            raise NotImplementedError

        return A_row.T

    def generate_A_tran_diag(self):
        """Create A_tran_diag"""

        diag = np.eye(self.num_connections)
        vec = np.zeros(self.num_connections)[:, None]
        for i, ele in enumerate(self.parameter['cable']):
            vec[i] = -ele['R'] / ele['L']
        A_tran_diag = vec * diag

        return A_tran_diag

    def generate_A_load_col(self, load_i):

        A_load_col = np.zeros(self.num_connections)

        CM_row = self.CM[(self.num_source - 1) + load_i]

        indizes = list(CM_row[CM_row != 0])  # get entries unequal 0
        signs = np.sign(indizes)  # get signs

        indizes_ = indizes * signs  # delet signs from indices
        indizes_.astype(dtype=np.int32)

        C_sum = 0

        for _, ele in enumerate(self.parameter['cable']):
            C_sum += ele['C']

        for _, (idx, sign) in enumerate(zip(indizes_, signs)):
            idx = int(idx)
            A_load_col[idx - 1] = sign * -(C_sum ** -1)

        return A_load_col

    def generate_A_load_row(self, load_i):

        A_load_row = np.zeros(self.num_connections)

        CM_col = self.CM[(self.num_source - 1) + load_i]

        indizes = list(CM_col[CM_col != 0])  # get entries unequal 0

        signs = np.sign(indizes)  # get signs
        indizes_ = indizes * signs  # delet signs from indices

        for i, (idx, sign) in enumerate(zip(indizes_, signs)):
            idx = int(idx)

            A_load_row[idx - 1] = sign * 1 / self.parameter['cable'][idx - 1]['L']

        return A_load_row

    def generate_A_load_diag(self):
        diag = np.eye(self.num_load)
        vec = np.zeros(self.num_load)

        for i, ele in enumerate(self.parameter['load']):
            CM_row = self.CM[(self.num_source) + i]
            indizes = list(CM_row[CM_row != 0])
            signs = np.sign(indizes)  # get signs
            indizes_ = indizes * signs  # delet signs from indices
            C_sum = 0
            for _, idx in enumerate(indizes_):
                idx = int(idx)

                C_sum += self.parameter['cable'][idx - 1]['C']

            vec[i] = - (ele['R'] * (C_sum)) ** -1

        A_load_diag = vec * diag

        return A_load_diag

    def generate_A(self):
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
        self.num_fltr = 4 * self.num_LCL + 2 * self.num_LC + 2 * self.num_L
        A_source = np.zeros((self.num_fltr, self.num_fltr))  # construct matrix of zeros
        A_source_list = [self.get_A_source(i) for i in range(1, self.num_source + 1)]

        for i, ele in enumerate(A_source_list):
            if i < self.num_LCL:
                start = 4 * i
                stop = 4 * i + 4
                A_source[start:stop, start:stop] = ele

            elif i < self.num_LCL + self.num_LC:
                start = 2 * i + 2 * self.num_LCL
                stop = 2 * i + 2 + 2 * self.num_LCL
                A_source[start:stop, start:stop] = ele

            elif i < self.num_LCL + self.num_LC + self.num_L:
                start = 2 * i + 2 * self.num_LCL
                stop = 2 * i + 2 + 2 * self.num_LCL
                A_source[start:stop, start:stop] = ele

        # get A_col
        A_col = np.zeros((self.num_fltr, self.num_connections))
        A_col_list = [self.get_A_col(i) for i in range(1, self.num_source + 1)]  # start at 1 bc Source 1 ...

        for i, ele in enumerate(A_col_list):
            if i < self.num_LCL:
                start = 4 * i
                stop = 4 * i + 4
                A_col[start:stop, :] = ele

            elif i < self.num_LCL + self.num_LC:
                start = 2 * i + 2 * self.num_LCL
                stop = 2 * i + 2 + 2 * self.num_LCL
                A_col[start:stop, :] = ele

            elif i < self.num_LCL + self.num_LC + self.num_L:
                start = 2 * i + 2 * self.num_LCL
                stop = 2 * i + 2 + 2 * self.num_LCL
                A_col[start:stop, :] = ele

        # get A_row
        A_row = np.zeros((self.num_connections, self.num_fltr))
        A_row_list = [self.get_A_row(i) for i in range(1, self.num_source + 1)]  # start at 1 bc Source 1 ...

        for i, ele in enumerate(A_row_list):
            if i < self.num_LCL:
                start = 4 * i
                stop = 4 * i + 4
                A_row[:, start:stop] = ele

            elif i < self.num_LCL + self.num_LC:
                start = 2 * i + 2 * self.num_LCL
                stop = 2 * i + 2 + 2 * self.num_LCL
                A_row[:, start:stop] = ele

            elif i < self.num_LCL + self.num_LC + self.num_L:
                start = 2 * i + 2 * self.num_LCL
                stop = 2 * i + 2 + 2 * self.num_LCL
                A_row[:, start:stop] = ele

        A_tran_diag = self.generate_A_tran_diag()

        A_load_row_list = list()
        for i in range(self.num_load):
            A_load_row_list.append(self.generate_A_load_row(i + 1))
        A_load_row = np.vstack(A_load_row_list).transpose()  # i-> idx // i+1 -> num of load

        A_load_col_list = list()
        for i in range(self.num_load):
            A_load_col_list.append(self.generate_A_load_col(i + 1))
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

    def generate_B(self):
        """Generate the B matrix
        
        The previously constructed matrices are now plugged together in the form:
            [[B_source,        0, ...,         0],
             [       0, B_source, ...,         0],
             [       0,        0, ...,         0],
             [       0,        0, ...,  B_source]]
        Returns:
            B: B matrix for state space (2*num_source+num_connections,num_source)
        """
        B = np.zeros((self.num_fltr + self.num_connections + self.num_load, self.num_source))

        B_source_list = [self.get_B_source(i) for i in range(1, self.num_source + 1)]  # start at 1 bc Source 1 ...

        for i, ele in enumerate(B_source_list):
            if i < self.num_LCL:
                start = 4 * i
                stop = 4 * i + 4
                B[start:stop, i:i + 1] = ele

            elif i < self.num_LCL + self.num_LC:
                start = 2 * i + 2 * self.num_LCL
                stop = 2 * i + 2 + 2 * self.num_LCL
                B[start:stop, i:i + 1] = ele

            elif i < self.num_LCL + self.num_LC + self.num_L:
                start = 2 * i
                stop = 2 * i + 2
                B[start:stop, i:i + 1] = ele

        return B

    def generate_C(self):
        """Generate the C matrix
        
        Retruns:
            C: Identity matrix (2*num_source+num_connections)
        """
        return np.eye(self.num_fltr + self.num_connections + self.num_load)

    def generate_D(self):
        """Generate the D vector
        
        Retruns:
            0: Zero vector (2*num_source+num_connections)
        """
        return 0

    def get_sys(self):
        """Returns state space matrices"""

        A = self.generate_A()
        B = self.generate_B()
        C = self.generate_C()
        D = self.generate_D()
        return (A, B, C, D)

    def get_states(self):
        states = list()
        for s in range(1, self.num_source + 1):
            if s < self.num_LCL:
                states.append(f'i_f{s}')
                states.append(f'u_f{s}')
                states.append(f'i_{s}')
                states.append(f'u_{s}')

            elif s < self.num_LCL + self.num_LC + self.num_L:
                states.append(f'i_{s}')
                states.append(f'u_{s}')

        for c in range(1, self.num_connections + 1):
            states.append(f'i_c{c}')

        for l in range(1, self.num_load + 1):
            states.append(f'u_l{l}')
        return states

    def draw_graph(self):
        """Plots a graph according to the CM matrix
        
        Red nodes corresponse to a source.
        Lightblue nodes corresponse to a load.
        """

        edges = []
        color = []
        for i in range(1, self.num_connections + 1):
            (row, col) = np.where(self.CM == i)
            (row_idx, col_idx) = (row[0] + 1, col[0] + 1)
            edges.append((row_idx, col_idx))
            if row_idx <= self.num_source:
                color.append('red')
            else:
                color.append('blue')

        G = nx.Graph(edges)

        color_map = []

        for node in G:
            if node <= self.num_source:
                color_map.append('red')
            else:
                color_map.append('lightblue')

        nx.draw(G, node_color=color_map, with_labels=True)
        plt.show()

        pass
