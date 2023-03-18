'''
１、レポットコード内すべて関数名と変数名を抽出する。
２、関数に対してローカル変数及び関して構文木を抽出する。（所在行数と所在振り返り操作）
３、関数の構文木を抽出する。
'''

import ast
import builtins


import glob
import pandas as pd
import keyword
import networkx as nx
import node_to_vec as n2v

class CodeTransformer(ast.NodeTransformer):
  '''
  params:
  func_name, var_name, for_name : to save name of function, var and for

  '''
  def __init__(self):
    self.func_name, self.var_name, self.for_name = [], [], []  # to save name of function, var and for 
    self.var_in_func = {}                                      # to save var in which function without subfunction
    self.name_line = {}                                        # to save var in which line
    self.target_var = None                                     # which target var is tracked at the moment
    self.func = ""                                             # which function is used at the moment
    self.check_func_sublist = {}                               # to save subfunction in which function
    self.target_loop = None                                    # which target loop that var in is tracked at the moment
    self.loop_type = ['For','AsyncFor','While','Try']          
    self.target_def = None                                    # which target function define that var in is tracked at the moment

  '''
  ASTの走査
  '''
  def get_func_name(self, func_id:str):
    if func_id not in self.func_name:
      self.func_name.append(func_id)

  def visit_FunctionDef(self, node):
    self.func = node.name
    self.get_func_name(node.name)  #関数名を抽出する
    self.generic_visit(node)
    self.get_var_in_func(node)
    return node
  
  def visit_For(self, node):
    try:
      self.get_for_name(node.target.id)
    except:
      pass 
    self.generic_visit(node)
    return node  


  def get_for_name(self, for_id:str):
    '''
    for文の臨時変数を抽出する
    params:
    for_id:for文の臨時変数。 for i in range(10) のi
    '''
    if for_id not in self.for_name :
      self.for_name.append(for_id)  #for文の臨時変数を抽出する
    if for_id in self.var_name:
      self.var_name.remove(for_id)  #変数名中保存したfor文の臨時変数を削除する

  
  def get_var_name(self, var_id:str):
    '''
    変数名を抽出する
    '''
    if var_id not in ( set(keyword.kwlist) | set(dir(builtins))):  #キーワードまたは関数名かどうかを判定する
      if var_id in set(self.func_name):
        if self.func not in self.check_func_sublist.keys():
          self.check_func_sublist[self.func] = [var_id]
        elif var_id not in self.check_func_sublist[self.func]:
          self.check_func_sublist[self.func].append(var_id)
      elif var_id not in self.for_name:     #for文の臨時変数かどうかを判定する
        self.var_name.append(var_id)
        return var_id

  
  def get_var_in_func(self, node):
    '''
    各関数内変数名を抽出する
    '''
    func_name = self.func
    for child in ast.iter_child_nodes(node):
      if type(child).__name__ == "Name":
        var_id = self.get_var_name(child.id)        
        if var_id != None:          
          if func_name not in  self.var_in_func.keys():
            self.var_in_func[func_name] = [var_id]
          elif child.id not in self.var_in_func[func_name]:
            self.var_in_func[func_name].append(var_id)
          self.get_var_name_line(child)
      self.get_var_in_func(child)

  def get_var_name_line(self, node):
    '''
    変数所在行数を抽出する
    '''
    if hasattr(node, 'id'):
      for key, value in self.var_in_func.items():
        if key in self.name_line.keys():
          var_line = self.name_line[key]
        else:
          var_line = {}
        if self.func == key:
          if node.id in value:
            if type(node.id) == type(''):
              if node.id not in var_line.keys():
                var_line[node.id] = [node.lineno] 
              elif node.lineno not in var_line[node.id]:
                var_line[node.id].append(node.lineno)
            self.name_line[key] = var_line
    else:
      pass

  def track_line(self, node, line):
    '''
    対応した変数の所在行数の構文木を抽出する
    '''
    if hasattr(node, "lineno"):
      if line != node.lineno:
        for child in ast.iter_child_nodes(node):
          self.track_line(child,line)  
      else:
        self.target_var = node
        pass
    else:
      for child in ast.iter_child_nodes(node):
          self.track_line(child,line) 

  def track_loop(self, node, line):
    '''
    対応した変数の所在ループの構文木を抽出する
    '''
    if type(node).__name__ in self.loop_type:
      if hasattr(node,'end_lineno'):
        if line <= node.end_lineno and line >= node.lineno:
          self.target_loop = node
    else:
      for child in ast.iter_child_nodes(node):
          self.track_loop(child,line) 

  def track_def(self, node, line):
    '''
    対応した変数の所在関数の構文木を抽出する
    '''
    if type(node).__name__ == 'FunctionDef':
      if hasattr(node,'end_lineno'):
        if line <= node.end_lineno and line >= node.lineno:
          self.target_def = node
    else:
      for child in ast.iter_child_nodes(node):
          self.track_def(child,line) 


def merge_func(check_func, var_in_func, func_list):
  for func_name in func_list:
    if func_name in check_func.keys():
      for i in check_func[func_name]:
        try:
          for j in var_in_func[i]: 
            if j not in var_in_func[func_name]:       
              var_in_func[func_name].append(j)
          del var_in_func[i] 
        except Exception as r:
          pass

def counter(dict_func, var_in_func):
  for key, value in var_in_func.items():
    if key in dict_func.keys():
      var_counter = dict_func[key]
    else:
      var_counter = {}
    for word in value:
      if word not in var_counter.keys():
        var_counter[word] = 1
      elif word in var_counter.keys():
        var_counter[word] += 1
    dict_func[key] = var_counter
  return dict_func

def filter_var(dict_func):
  for key, value in list(dict_func.items()):
    for var in list(value.keys()):
      if value[var] <= 5:
        del value[var]
    if dict_func[key]:
      pass
    else:
      del dict_func[key]

if __name__ == "__main__":
  var, for_var, func_var, func_params, func_return = {}, {}, {}, {}, {}
  dict_func, var_counter = {},{}
  var_to_id, func_to_id = {},{}
  id_to_var, id_to_func = {},{}
  node_to_id = {}
  id_to_node = {}
  node_to_id, id_to_node = n2v.create_node_lib() 


  paths = '/Users/wintor7/report7/report7_2020/e205744/report7.py'

  path = '/Users/wintor7/report7/'

  pyfile = glob.glob(path + 'report7**/**/report7.py')
  
  for file in pyfile:
    try:
      with open(file, 'r') as fh:
        content = fh.read()

        #抽取AST
      #print(file)
      r_node = ast.parse(content)

      transformer = CodeTransformer()
      r_node = transformer.visit(r_node)
    
      merge_func(transformer.check_func_sublist, transformer.var_in_func, transformer.func_name)
      dict_func = counter(dict_func, transformer.var_in_func)
    except SyntaxError:
      continue
  filter_var(dict_func)
    #print(student_id, transformer.var_in_func)

  num = 0
  loop_num = 0
  def_num = 0
  for file in pyfile:
    #print(file)
    with open(file, 'r') as fh:
      content = fh.read()
      try:
        r_node = ast.parse(content)
        transformer = CodeTransformer()
        r_node = transformer.visit(r_node)
      except SyntaxError:
        #print(file)
        continue



      name_line = transformer.name_line
      node_list = {}
      #print('name_line:', name_line)
      
      #print('node_list:', node_list)
      del_list = []
      for key in name_line.keys():            #筛选是否为常见变量名称
        temp = {}
        if key not in dict_func.keys():
          del_list.append(key)
        else:
          for var in dict_func[key]:
            if var in name_line[key]:
              temp[var] = name_line[key][var]
        name_line[key] = temp
      print(name_line)
      print(file)

      for key in del_list:
        del name_line[key]
      
      for key in name_line.keys():                                    #记录各变量的AST
        temp_list = {}
        for var, value in name_line[key].items():
          for i in value:
            transformer.track_line(r_node, i)
            if var not in temp_list.keys():
              temp_list[var] = [transformer.target_var]
            elif transformer.target_var not in temp_list[var]:
              temp_list[var].append(transformer.target_var)
        node_list[key] = temp_list

        loop_list = {}        #
        loop_temp_list = {}
        for var, value in name_line[key].items():
          for i in value:
            transformer.track_loop(r_node,i)
            if var not in loop_temp_list.keys():
              loop_temp_list[var] = [transformer.target_loop]
            elif transformer.target_loop not in loop_temp_list[var]:
              loop_temp_list[var].append(transformer.target_loop)
        loop_list[key] = loop_temp_list 
        #print('loop_list:', loop_list)


      def_list = {}      #
      def_temp_list = {}
      for var, value in name_line[key].items():
        for i in value:
          transformer.track_def(r_node,i)
          if var not in def_temp_list.keys():
            def_temp_list[var] = [transformer.target_def]
          elif transformer.target_def not in def_temp_list[var]:
            def_temp_list[var].append(transformer.target_def)
      def_list[key] = def_temp_list

      #print('def_list:', def_list)
      func_list = list(transformer.var_in_func.keys())
      var_list = []
      for i,v in enumerate(transformer.var_in_func):
        for i in transformer.var_in_func[v]:
          var_list.append(i)
      
      var_to_id, id_to_var = n2v.name_corpus(var_list, var_to_id, id_to_var)
      func_to_id, id_to_func = n2v.name_corpus(func_list, func_to_id, id_to_func)

      

      var_in_func = transformer.var_in_func
      #print('var_in_func: ', var_in_func)
      #print('name_line:', transformer.name_line)
      #print('node_list:', node_list)
      for func in var_in_func.keys():
        label1 = func
        for var in var_in_func[func]:
          label2 = var
          graph = nx.DiGraph(label1 = label1, label2 = label2)
          str_to_node = {}
          #print(func)
          #print(var)
          #print(file)
          try:
            for var_node in node_list[func][var]:
              root = len(str_to_node)
              n2v.create_graph(var_node, node_to_id, graph, str_to_node, root)
              for node in graph.nodes():
                graph.nodes[node]['feature'] = str_to_node[node]
              root += 1
            nx.write_gpickle(graph,'/Users/wintor7/report7/graph/var/' + str(num) + '.gpickle') 
            num += 1           
          except KeyError:
          #  print(file)
            continue


          graph_loop = nx.DiGraph(label1 = label1, label2 = label2)
          str_to_node = {}
          try:
            for var_node in loop_list[func][var]:
              root = len(str_to_node)
              n2v.create_graph(var_node, node_to_id, graph_loop, str_to_node, root)
              for node in graph_loop.nodes():
                graph_loop.nodes[node]['feature'] = str_to_node[node]
              root += 1
            nx.write_gpickle(graph_loop,'/Users/wintor7/report7/graph/loop/' + str(loop_num) + '.gpickle')  
            loop_num += 1
          except KeyError:
            
            pass


          graph_def = nx.DiGraph(label1 = label1, label2 = label2)
          str_to_node = {}
          try:
            for var_node in def_list[func][var]:
              root = len(str_to_node)
              n2v.create_graph(var_node, node_to_id, graph_def, str_to_node, root)
              for node in graph_def.nodes():
                graph_def.nodes[node]['feature'] = str_to_node[node]
              root += 1
            nx.write_gpickle(graph_def,'/Users/wintor7/report7/graph/def/' + str(def_num) + '.gpickle') 
            def_num += 1
          except KeyError:
            pass  


def creat_ASTgraph(some_list, node_to_id, graph, str_to_node, path, var):
  graph = nx.DiGraph(label1 = label1, label2 = label2)
  str_to_node = {}
  for var_node in some_list[var]:
    root = len(str_to_node)
    n2v.create_graph(var_node, node_to_id, graph, str_to_node, root)
    for node in graph.nodes():
      graph.nodes[node]['feature'] = str_to_node[node]
    root += 1
  nx.write_gpickle(graph,path + str(label1) + '_' + str(label2) + '.gpickle')  
