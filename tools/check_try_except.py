import ast, sys
p='C:/dev/GenA-I2.0/bot_v3.py'
with open(p,'r',encoding='utf-8') as f:
    src=f.read()
try:
    tree=ast.parse(src)
except Exception as e:
    print('PARSE ERR',e)
    sys.exit(1)

class Finder(ast.NodeVisitor):
    def visit_Try(self,node):
        types=[]
        for h in node.handlers:
            if h.type is None:
                types.append('Exception:bare')
            else:
                if isinstance(h.type, ast.Name):
                    types.append(h.type.id)
                else:
                    try:
                        types.append(ast.unparse(h.type))
                    except Exception:
                        types.append(str(type(h.type)))
        if 'Exception' in types or 'Exception:bare' in types:
            for i,t in enumerate(types):
                if t in ('Exception','Exception:bare'):
                    if i != len(types)-1:
                        print('Found try at line',node.lineno,'except order:',types)
                        break
        self.generic_visit(node)

Finder().visit(tree)
print('Done')
