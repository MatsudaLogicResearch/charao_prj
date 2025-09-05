#merge multiple markdown file in 1 file.
#

import re
import pandas as pd
from collections import defaultdict
import argparse, os, sys
from io import StringIO
from functools import reduce
import copy
#from tabulate import tabulate

def nested_dict():
    return defaultdict(nested_dict)

def parse_md_to_dict(md_text:str):
    h1 = "None"
    h2 = "None"
    h3 = "None"
    table_lines = []
    cell_data = nested_dict()

    lines = md_text.splitlines()
    for line in lines:
      
      #-- convert table data to DF & hold
      if line == "" and len(table_lines):
        df      = parse_table(table_lines)
        cell_data[h1][h2][h3] = df
        #print(f"h1={h1}, h2={h2}, h3={h3}")
        table_lines=[]
        continue
      
      #-- skip line
      if not line.startswith(("#","|")):
        continue

      #-- heading
      if line.startswith("# "):  # Liberty setting/ Cell Infomation
        h1= line.strip().split()[1]
        h2 = "None"
        h3 = "None"
        table_lines = []

      elif line.startswith("## "):  #  units / cell name 
        h2 = line.strip().split()[1]
        h3 = "None"
        table_lines = []
        
      elif line.startswith("### "):  #  attributes
        h3 = line.strip().split()[1]
        table_lines = []

      #-- get table line
      if line.startswith("|"):
        table_lines.append(line)

    return cell_data

def parse_table(table_lines):
  #-- remove "|-" line & remove " "
  table = [x.replace(" ","").lstrip("|").rstrip("|")  for x in table_lines if not x.startswith("|-")]
  table_text="\n".join(table)
  df = pd.read_csv(StringIO(table_text), sep="|", header=0, engine='python', skipinitialspace=True, dtype=str)
  df = df.drop(columns=['']) if '' in df.columns else df
  df = df.dropna(how='all')  # 空行削除

  #空白削除
  for col in df.columns:
    if df[col].dtype == object:
      df[col] = df[col].map(lambda x: re.sub(r"\s+", "", x) if isinstance(x, str) else x)
        
  #print(df)
  return df

def merge_df_cell(val1, val2):
    merged = []

    for v1, v2 in zip(val1, val2):
        vals = [v for v in (v1, v2) if v is not None and not pd.isna(v)]
        vals_str = [str(v) for v in vals]
        
        # 数値判定（両方が数値に変換できる場合）
        is_both_numeric = all(is_number(s) for s in vals_str)

        if is_both_numeric:
            # 数値なら常に \ で連結（重複してても）
            #merged_val = " \\ ".join(vals_str)
            merged_val = " \\newline ".join(vals_str)
        else:
            # 文字列なら重複排除して連結（順序維持）
            unique_vals = list(dict.fromkeys(vals_str))
            #merged_val = unique_vals[0] if len(unique_vals) == 1 else " \\ ".join(unique_vals)
            merged_val = unique_vals[0] if len(unique_vals) == 1 else " \\newline ".join(unique_vals)

        merged.append(merged_val)

    return pd.Series(merged, index=val1.index)

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def merge_cell_tables(input_md:list[str], dict_list:list[dict]):
  rslt_data = nested_dict()

  if   len(dict_list)==1:
    rslt_data=copy.deepcopy(dict_list[0])

  elif len(dict_list) >1:
    keys_h1=dict_list[0].keys()
    for i,d in zip(input_md, dict_list):
      keys = sorted(d.keys())
      if (keys != sorted(keys_h1)):
        print(f"[ERR] h1 size is missmatch.")
        print(f"        file={i}")
        print(f"        key()={keys}")
        print(f"        exp  ={keys_h1}")
        sys.exit()

    #-------------------------------
    for h1 in keys_h1:   #--- no sorted
      # check h2 key
      keys_h2=dict_list[0][h1].keys()
      
      for i,d in zip(input_md, dict_list):
        keys = sorted(d[h1].keys())
        if (keys != sorted(keys_h2)):
          print(f"[ERR] h2 size is missmatch.")
          print(f"        file={i}")
          print(f"        key()={keys}")
          print(f"        exp  ={keys_h2}")
          sys.exit()

      #-------------------------------
      for h2 in keys_h2:   #-- no sorted
        # check h3 key
        keys_h3=dict_list[0][h1][h2].keys()
      
        for i,d in zip(input_md, dict_list):
          keys = sorted(d[h1][h2].keys())
          if (keys != sorted(keys_h3)):
            print(f"[ERR] h3 size is missmatch.")
            print(f"        file={i}")
            print(f"        key()={keys}")
            print(f"        exp  ={keys_h3}")
            sys.exit()

        #-------------------------------
        for h3 in keys_h3:   #-- no sorted

          # compare dataframe
          df_list=[x[h1][h2][h3] for x in dict_list]

          rslt_data[h1][h2][h3] = reduce(lambda a,b: a.combine(b, merge_df_cell), df_list)

  #
  return rslt_data


def markdown_table_with_linebreaks(df):
    split_cells = df.apply(lambda col: col.map(lambda x: str(x).split('\\newline')))
    max_lines_per_row = split_cells.apply(lambda col: col.map(len)).max(axis=1)
    
    headers = df.columns.tolist()

    # 各列の最大幅を計算
    col_widths = []
    for col in headers:
        # ヘッダー文字数
        max_len = len(col)
        # データの中で最長の行文字数を探す
        col_cells = split_cells[col]
        for cell_lines in col_cells:
            for line in cell_lines:
                if len(line) > max_len:
                    max_len = len(line)
        col_widths.append(max_len)
    
    # ヘッダー行（右パディングで幅を合わせる）
    header_line = '| ' + ' | '.join(h.ljust(w) for h, w in zip(headers, col_widths)) + ' |'
    # 区切り線
    separator_line = '| ' + ' | '.join('-' * w for w in col_widths) + ' |'
    
    output_lines = [header_line, separator_line]
    
    for idx, row in split_cells.iterrows():
        max_lines = max_lines_per_row[idx]
        for i in range(max_lines):
            line_cells = []
            for cell, width in zip(row, col_widths):
                line = cell[i] if i < len(cell) else ''
                line_cells.append(line.ljust(width))  # 右パディングで幅合わせ
            output_lines.append('| ' + ' | '.join(line_cells) + ' |')
    
    return '\n'.join(output_lines)

#def markdown_table_with_linebreaks(df):
#    # 各セルを \newline で分割しリストに変換（列ごとに map を使う）
#    split_cells = df.apply(lambda col: col.map(lambda x: str(x).split('\\newline')))
#    
#    max_lines_per_row = split_cells.apply(lambda col: col.map(len)).max(axis=1)
#    
#    headers = df.columns.tolist()
#    header_line = '| ' + ' | '.join(headers) + ' |'
#    separator_line = '| ' + ' | '.join(['-' * len(h) for h in headers]) + ' |'
#    
#    output_lines = [header_line, separator_line]
#    
#    for idx, row in split_cells.iterrows():
#        max_lines = max_lines_per_row[idx]
#        for i in range(max_lines):
#            line_cells = []
#            for cell in row:
#                line_cells.append(cell[i] if i < len(cell) else '')
#            output_lines.append('| ' + ' | '.join(line_cells) + ' |')
#    
#    return '\n'.join(output_lines)


def gen_markdown(output_md, rslt_data):
    
  with open(output_md, "w") as f:

    #f.write(f"---\n")
    #f.write(f"header-includes:\n")
    #f.write(f"  - \\usepackage{{tabularx}}\n")
    #f.write(f"  - \\usepackage{{booktabs}}\n")
    #f.write(f"  - \\let\\tabular\\tabularx\n")
    #f.write(f"  - \\let\\endtabular\\endtabularx\n")
    #f.write(f"  - \\def\\tabularxcolumn#1{{m{{#1}}}}\n") # 垂直中央揃え
    #f.write(f"  - \\setlength{{\\tabcolsep}}{{4pt}}\n")  # セル内余白
    #f.write(f"  - \\renewcommand{{\\arraystretch}}{{1.2}}\n")  # 行間
    #f.write(f"---\n")
      
    for h1 in rslt_data.keys():
      # write header
      f.write(f"# {h1}\n")
      f.write("\n")
      
      for h2 in rslt_data[h1].keys():
        # write header
        if h2 != "None":
          f.write(f"## {h2}\n")
          f.write("\n")
            
        for h3 in rslt_data[h1][h2].keys():
          # write header
          if h3 != "None":
            f.write(f"### {h3}\n") 
            f.write("\n")
            
          ## check dataframe
          df = rslt_data[h1][h2][h3]
          if df is None:
              continue
          
          ##  create markdown-table from dataframe, write 
          #md_table = tabulate(df, headers='keys', tablefmt='github', showindex=False)
          md_table=markdown_table_with_linebreaks(df)
          f.write(md_table)
          f.write("\n\n")
  
    

def main():
  parser = argparse.ArgumentParser(description='argument')
  parser.add_argument('-i','--input_md' , type=str, nargs="*",default=["input.md"] ,help='list of input markdown files')
  parser.add_argument('-o','--output_md', type=str           ,default="output.md"  ,help='output markdown file.')
  args = parser.parse_args()
    
  input_md =args.input_md
  output_md=args.output_md
  #-- check input files
  for i in input_md:
    if os.path.isfile(i):
      print (f" [INF]: input md={i}")
    else:
      print (f" [ERR]: not found input md={i}")
      sys.exit()
  
  # Markdownファイル読み込み & parse
  md_dict_list=[]
  for i in input_md:
    with open(i, "r", encoding="utf-8") as f:
      md     = f.read()
      md_dict = parse_md_to_dict(md_text=md)
      md_dict_list.append(md_dict)

  # Merge
  merge_result = merge_cell_tables(input_md=input_md, dict_list=md_dict_list)

  # generate markdown
  gen_markdown(output_md=output_md, rslt_data=merge_result)

if __name__ == '__main__':
 main()
