import xml.etree.ElementTree
import xml.etree.ElementTree as ET

from collections import OrderedDict as odict

import math


BEZIER_STEPS = 50

svg_tpl = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!-- Created with Inkscape (http://www.inkscape.org/) -->

<svg
   xmlns:dc="http://purl.org/dc/elements/1.1/"
   xmlns:cc="http://creativecommons.org/ns#"
   xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
   xmlns:svg="http://www.w3.org/2000/svg"
   xmlns="http://www.w3.org/2000/svg"
   xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
   xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
   width="210mm"
   height="297mm"
   viewBox="0 0 210 297"
   version="1.1"
   id="svg44"
   inkscape:version="0.92.2 2405546, 2018-03-11"
   sodipodi:docname="a.svg">
  <defs
     id="defs38" />
  <sodipodi:namedview
     id="base"
     pagecolor="#ffffff"
     bordercolor="#666666"
     borderopacity="1.0"
     inkscape:pageopacity="0.0"
     inkscape:pageshadow="2"
     inkscape:zoom="1.3833896"
     inkscape:cx="295.70367"
     inkscape:cy="931.88214"
     inkscape:document-units="mm"
     inkscape:current-layer="layer1"
     showgrid="false" />
  <metadata
     id="metadata41">
    <rdf:RDF>
      <cc:Work
         rdf:about="">
        <dc:format>image/svg+xml</dc:format>
        <dc:type
           rdf:resource="http://purl.org/dc/dcmitype/StillImage" />
        <dc:title></dc:title>
      </cc:Work>
    </rdf:RDF>
  </metadata>
  <g
     inkscape:label="Layer 1"
     inkscape:groupmode="layer"
     id="layer1">
  </g>
</svg>
'''


class vec2:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def copy(self):
        return vec2(self.x, self.y)

    @property
    def cs(self):
        return (self.x, self.y)

    def __getitem__(self, i):
        if i >= 2 or i < 0:
            raise IndexError()
        return self.x if i == 0 else self.y

    def __len__(self):
        return 2

    def __neg__(self):
        return vec2(-self.x, self.y)
    def __add__(self, o):
        return vec2(self.x + o.x, self.y + o.y)

    def __sub__(self, o):
        return vec2(self.x - o.x, self.y - o.y)

    def __mul__(self, t):
        return vec2(self.x * t, self.y * t)

    def __truediv__(self, t):
        t = 1 / t
        return vec2(self.x * t, self.y * t)

    def __iadd__(self, o):
        self.x += o.x
        self.y += o.y
        return self

    def __isub__(self, o):
        self.x -= o.x
        self.y -= o.y
        return self

    def __imul__(self, t):
        self.x *= t
        self.y *= t
        return self

    def __itruediv__(self, o):
        self.x /= o
        self.y /= o
        return self

    def vmul(self, o):
        return vec2(self.x * o.x, self.y * o.y)

    def ivmul(self, o):
        self.x *= o.x
        self.y *= o.y

    def set(self, o):
        self.x = o.x
        self.y = o.y

    def __repr__(self):
        return 'vec2(%s, %s)' % (self.x, self.y)


def dot(a, b):
    return a.x * b.x + a.y * b.y


def length(v):
    return math.sqrt(dot(v, v))


def interp(t, a, b):
    return a * (1 - t) + b * t


MOVE = 'm'
LINE = 'l'
QUADRATIC_BEZIER = 'q'
HORIZONTAL_LINE = 'h'
VERTICAL_LINE = 'v'
CLOSE = 'z'
NULL = None

RELATIVE = 'rel'
ABSOLUTE = 'abs'

modes = dict(m=MOVE, l=LINE, h=HORIZONTAL_LINE, v=VERTICAL_LINE, q=QUADRATIC_BEZIER, z=CLOSE)


def get_mode(t):
    if t in modes:
        return modes[t]
    return None


def decasteljau(ps, t):
    if len(ps) == 1:
        return ps[0].copy()
    r = []
    for i, p in enumerate(ps[:-1]):
        n = p * (1 - t) + ps[i + 1] * t
        r.append(n)
    #print(t, r)
    return decasteljau(r, t)


def render_bezier(bezier, N):
    ps = []
    #print('Q:',  bezier)
    for i in range(N):
        t = i / (N - 1)
        p = decasteljau(bezier, t)
        ps.append(p.copy())
    #print('R: ', ps)
    return ps


def parse_path(tokens):
    #print('\n'.join(tokens[:20]))
    mode = NULL
    rel_mode = ABSOLUTE

    paths = []
    commands = []
    command = MOVE, ABSOLUTE, []
    for T in tokens:
        t = T.lower()
        new_mode = get_mode(t)
        if new_mode is not None:
            if command[-1]:
                commands.append(command)

            mode = new_mode
            rel_mode = RELATIVE if T.lower() == T else ABSOLUTE
            command = (mode, rel_mode, [])
            if mode in (CLOSE, MOVE) and commands:
                commands.append(command)
                paths.append(commands)
                commands = []
        else:
            command[-1].append(T)
    assert(not command[-1])
    # can be unclosed
    if commands:
        paths.append(commands)

    
    pos = vec2(0, 0)
    rs = []
    r = []
    last_command = None
    for commands in paths:
        for command in commands:
            mode, rel_mode, tokens = command

            if mode == CLOSE:
                # # TODO add last point
                r.append(r[0].copy())
                # TODO z may use current pos to complete prev command *sigh*
                #handle(pos)
                

            bezier = [pos]

            for itoken, token in enumerate(tokens):
                is_last_token = itoken == len(tokens) - 1
                    
                op = lambda a, b: b if rel_mode is ABSOLUTE else a + b

                org = pos
                new = pos.copy()

                if ',' in token:
                    x, y = [float(v) for v in token.split(',')]
                    new.x = op(new.x, x)
                    new.y = op(new.y, y)
                else:
                    assert(mode in (HORIZONTAL_LINE, VERTICAL_LINE))
                    v = float(token)
                    if mode == HORIZONTAL_LINE:
                        new.x = op(new.x, v)
                    else:
                        new.y = op(new.y, v)
                        
                #print(org, ' -> ', new)

                if mode == MOVE:
                    mode = LINE
                    pos = new
                elif mode in (LINE, VERTICAL_LINE, HORIZONTAL_LINE):
                    if not r or r[-1] is not pos:
                        r.append(pos)
                    r.append(new)
                elif mode == QUADRATIC_BEZIER:
                    bezier.append(new)
                    if len(bezier) == 3:
                        r += render_bezier(bezier, BEZIER_STEPS + 1)
                        bezier.pop(0)
                else:
                    raise Exception()
            #print('%s resetting pos to %s' % (mode, new))
            pos = new
        if r:
            rs.append(r)
            r = []
        last_command = command    


    assert(not r)
    return rs
                    

def points_to_path(ps):
    return 'M ' + ' '.join(['%s,%s' % (p.x, p.y) for p in ps]) + ''


svg_ns = dict(svg='http://www.w3.org/2000/svg'
              , inkscape='http://www.inkscape.org/namespaces/inkscape'
              , sodipodi='http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd')


def parse(f):
    ns = svg_ns
    for k, v in ns.items():
        ET.register_namespace(k, v)
    ET.register_namespace('', ns['svg'])
    e = xml.etree.ElementTree.parse(f).getroot()

    r = []
    for path in e.findall('.//svg:path', ns):
        path = path.attrib['d']
        paths = (parse_path(path.split()))
        r.append(paths)

    return r


STEPS = 500

STEP = 0.5

if __name__ == '__main__':
    import sys

    #font_t = float(sys.argv[1])

    path_files = [parse(f) for f in sys.argv[1:]]

    path_lens_files = []

    for path_els in path_files:
        for paths in path_els:
            for ipath, path in enumerate(paths):
                print('move %s %s' % (path[0].x, path[0].y))
                for p in path:
                    print('plot %s %s' % (p.x, p.y))
                #paths[ipath] = resampled

    #for path_els in zip(*path_files):
    #    for paths in zip(*path_els):
    #        print(paths)
    #        for ps in zip(*paths):
    #            print(path)



    out = xml.etree.ElementTree.fromstring(svg_tpl)
    out_node = out.find('svg:g', svg_ns)

    for paths in path_els:
        d = ' '.join([points_to_path(ps) for ps in paths])
        path_el = ET.SubElement(out_node,  'path', d=d, style='stroke-width:1')

    ET.ElementTree(out).write('out.svg')
