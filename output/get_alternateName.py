"""
This code aim to get alternative name of variable name via matching with assignment base on Word2Vec.
"""


import gensim.models as gm

w2v_model = gm.Word2Vec.load('model/w2v_doc.model')
ft_model = gm.FastText.load('model/ft_doc.model')

def get_similar(result):
  """
  If the alternative name similar higher than 0.8, it will return it. 
  """
  var = []
  var_sim = []
  for i in result:
    if i[1] > 0.8 :
      var.append(i[0])
      var_sim.append(i)
  return var, var_sim

def get_altName(Name_list:list):
  """
  matching with variable name by cosine similarity
  """
  namelist = [ name for name in Name_list.keys()]
  all_list = []
  for var in namelist:
    try:
      result = w2v_model.wv.most_similar(var,topn=10)
    except KeyError:
      #result = ft_model.wv.similar_by_word(var, topn=10)
      continue

    var_name, var_sim = get_similar(result)
    for i in var_name:
      all_list.append(i)
  
  return all_list


if __name__ == '__main__':
  Name_list = {'index': 60,
  'filenames': 36,
  'fh': 23,
  'filename': 6,
  'words': 8,
  'file': 7,}

  all_list = get_altName(Name_list)
  print(all_list)
  print(len(all_list))



  