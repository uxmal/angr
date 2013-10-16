import os
import subprocess
import sys
import logging
import pdb

logging.basicConfig()
l = logging.getLogger("names")
l.setLevel(logging.DEBUG)

class NameFields:
    def __init__(self, ntype, addr, fs_path, extrn_fs_path=None):
        self.ntype = ntype
        self.addr = addr
        self.fs_path = os.path.realpath(os.path.expanduser(fs_path))
        self.lib_name = self.fs_path.split("/")[-1]
        self.extrn_fs_path =  extrn_fs_path if extrn_fs_path else self.fs_path
        self.extrn_lib_name = self.extrn_fs_path.split("/")[-1] if extrn_fs_path else self.lib_name

class Names:
    def __init__(self, ida):
        self.__names = {}
        self.__addr = {}
        self.__ida = ida
        self.__filename = ida.get_filename()
        self.__get_names()
        self.__resolve_fs_path()

    # Gets all the names within a file
    def __get_names(self):
        p_ls = subprocess.Popen(["nm", "-D", self.__filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result_ls = p_ls.stdout.readlines()

        for ls_out in result_ls:
            lib_symbol = ls_out.split()
            if len(lib_symbol) >= 2:
                ntype = lib_symbol[0 if len(lib_symbol) == 2 else 1]
                if ntype == "N": #skipping debugging symbols
                    continue
                sym = lib_symbol[1 if len(lib_symbol) == 2 else 2]
                addr = self.__ida.idaapi.get_name_ea(0, sym)
                self.__names[sym] = NameFields(ntype, addr, self.__filename)
                self.__addr[addr] = sym


    def __resolve_fs_path(self):
        p_ldd = subprocess.Popen(["ldd", self.__filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result_ldd = p_ldd.stdout.readlines()

        for key in self.__names.keys():
            if self.__names[key].ntype != 'U':
                continue
            found = False
            for lld_out in result_ldd:
                lib_entry = lld_out.split()
                if ("=>" in lld_out and len(lib_entry) != 3) or len(lib_entry) == 2: # skipping virtual libraries
                    lib = lib_entry[2 if "=>" in lld_out else 0]
                    ls_nm = subprocess.Popen(["nm", "-D", lib], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    result_lsnm = ls_nm.stdout.readlines()
                    for ls_nm_out in result_lsnm:
                        lib_symbol = ls_nm_out.split()
                        if len(lib_symbol) >= 2 and lib_symbol[0 if len(lib_symbol) == 2 else 1] not in "UN?":
                            if key == lib_symbol[1 if len(lib_symbol) == 2 else 2]:
                                self.__names[key].ntype = 'E'
                                self.__names[key].extrn_fs_path = os.path.realpath(os.path.expanduser(lib))
                                self.__names[key].extrn_lib_name = self.__names[key].extrn_fs_path.split("/")[-1]
                                found = True
            if found == False:
                l.error("Extern function has not been matched with a valid shared libraries. Symbol: %s" %key)
                pdb.set_trace()

    def __getitem__(self, name):
        return self.__names[name]

    def __setitem__(self, name, value):
        self.__names[name] = value

    def keys(self):
        return self.__names.keys()

    def get_type(self, name):
        try:
            return self.__names[name].ntype
        except:
            return None

    def is_name(self, addr):
        if addr in self.__addr.keys():
            return True
        return False

    def get_name_by_addr(self, addr):
        try:
            sym = self.__addr[addr]
        except:
            sym = None
        return sym

    def get_fs_path(self, name):
        try:
            path = self.__names[name].fs_path
        except:
            path = None
        return path

    def get_lib_name(self, name):
        try:
            lib_name = self.__names[name].lib_name
        except:
            lib_name = None
        return lib_name

    def get_extrn_fs_path(self, name):
        try:
            path = self.__names[name].extrn_fs_path
        except:
            path = None
        return path

    def get_extrn_lib_name(self, name):
        try:
            lib_name = self.__names[name].extrn_lib_name
        except:
            lib_name = None
        return lib_name

    def get_addr(self, name):
        try:
            addr = self.__names[name].addr
        except:
            addr = None
        return addr