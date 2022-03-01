# -*- coding: utf-8 -*-
def parse_list(text, conv):
    return [conv(x) for x in text.split(",")]

def parse_dict(text, conv):
    key_value = lambda triple: tuple([triple[0],conv(triple[2])])
    return dict(key_value(x.partition("=")) for x in text.split(";"))

def parse_note(steps, notes, velos, artis):
    BPM,UNIT,NOTE,TEMP,VELO,ARTI = 0,1,2,3,4,5
    
    assert len(steps) > 0, "no step."
    midi = []
    
    buf = []
    for i, step in enumerate(steps):
        note = step[NOTE]
        velo = velos[step[VELO]]
        temp = step[TEMP]
        arti = artis[step[ARTI]]
        
        
        if note == ">":
            # hold
            duration = 60 * 1000 / float(step[BPM]) * 4 / float(step[UNIT])
            buf.append(("0", "0", "0", "0", duration, arti))
        elif note == "-":
            # silence
            if len(buf) > 0:
                midi.extend(flush_notes(buf, notes))    
                buf = []
            
            buf.append(("0", "0", "0", "0", "0", arti))
        else:
            if len(buf) > 0:
                midi.extend(flush_notes(buf, notes))
                buf = []
            
            try:
                duration = 60 * 1000 / float(step[BPM]) * 4 / float(step[UNIT])
            except ZeroDivisionError as e:
                print("[%d]:%f,%f" % (i, float(step[BPM]), float(step[UNIT])))
                #print e
            buf.append(("1", note, temp, velo, duration, arti))
    
    
    if len(buf) > 0:
        midi.extend(flush_notes(buf, notes))
        buf = []
        
        
    _midi = list(zip(*midi))
    return (list(_midi[0]), list(_midi[1]), list(_midi[2]), list(_midi[3]))

TEMPORARIES = {
               "~":13,
             "^":12,
             "'":11,
             ">":1,
             "-":0,
             "<":-1,
             "/":-11,
             "_":-12,
             ".":-13,
             "%":-24
             }
    
def flush_notes(buf, chars):
    FLG,NOTE,TEMP,VELO,DURA,ARTI = 0,1,2,3,4,5
    midi = []
    flg = buf[0][FLG]
    
    if flg == "0":
        for _ in range(len(buf)):
            midi.append(("0","0","0","0"))
    else:
        note = buf[0][NOTE]
        velo = buf[0][VELO]
        temp = buf[0][TEMP]
        arti = float(buf[0][ARTI])
        duration = sum(data[DURA] for data in buf)
        
        if arti < 0:
            # legato
            duration = duration - arti
        elif arti == 0:
            pass
        else:
            #stackate
            if duration - arti < arti:
                # アーティキュレーション分短くすると、アーティキュレーション自体よりも短くなる場合、
                # 半分だけ短くする。
                duration = duration - (arti / 2)
            else:
                duration = duration - arti
    
        midi.append(("1", "%f" % (float(chars[note]) + TEMPORARIES[temp]), "%f" % float(velo), "%f" % duration))
        for _ in range(len(buf) -1):
            midi.append(("0","0","0","0"))
    
    return midi

def parse_ctrl(steps, chars):
    BPM,UNIT,CTRL = 0,1,2
    BUF_FLG, BUF_CTRL, BUF_DURA = 0, 1, 2
    
    assert len(steps) > 0, "no step."
    midi = []
    # buf : [(ON|OFF, ctrl, duration), ...]
    buf = []
    
    for i, step in enumerate(steps):
        ctrl = step[CTRL]
        if ctrl == "<":
            # keep up.
            if len(buf) > 0:
                if buf[-1][BUF_FLG] in ("-", ">"):
                    midi.extend(flush_ctrl(buf, chars))
                    buf = []

                # hold
                duration = 60 * 1000 / float(step[BPM]) * 4 / float(step[UNIT])
                #buf.append(("<", "0", duration))
                buf.append(("<", "0", duration))
            else:
                # buf is empty.
                duration = 60 * 1000 / float(step[BPM]) * 4 / float(step[UNIT])
                buf.append(("<", "0", duration))
        elif ctrl == ">":
            # keep down.
            if len(buf) > 0:
                if buf[-1][BUF_FLG] in ("-", "<"):
                    assert False, "->, <> is non-sense."
                else:
                    # hold
                    duration = 60 * 1000 / float(step[BPM]) * 4 / float(step[UNIT])
                    #buf.append(("<", "0", duration))
                    buf.append((">", "0", duration))
            else:
                # buf is empty.
                assert False, "begin with '>' is non-sense."
        elif ctrl == "=":
            # keep same.
            if len(buf) > 0:
                if buf[-1][BUF_FLG] in ("-", "<", ">"):
                    assert False, "->, <> is non-sense."
                else:
                    # hold
                    duration = 60 * 1000 / float(step[BPM]) * 4 / float(step[UNIT])
                    #buf.append(("<", "0", duration))
                    buf.append(("=", "0", duration))
            else:
                # buf is empty.
                assert False, "begin with '>' is non-sense."
        elif ctrl == "-":
            # set default
            if len(buf) > 0:
                midi.extend(flush_ctrl(buf, chars))
                buf = []
            
            buf.append(("-", "0", 0))
        else:
            if len(buf) > 0:
                if i + 1 < len(steps) and steps[i+1][CTRL] != ">":
                    duration = 60 * 1000 / float(step[BPM]) * 4 / float(step[UNIT])
                    buf.append(("0", ctrl, duration))
                    midi.extend(flush_ctrl(buf, chars))
                    buf = []
                else:
                    duration = 60 * 1000 / float(step[BPM]) * 4 / float(step[UNIT])
                    buf.append(("1", ctrl, duration))
#            else:
            duration = 60 * 1000 / float(step[BPM]) * 4 / float(step[UNIT])
            buf.append(("1", ctrl, duration))
    
    if len(buf) > 0:
        midi.extend(flush_ctrl(buf, chars))
        buf = []
        
    _midi = list(zip(*midi))
    return (list(_midi[0]), list(_midi[1]), list(_midi[2]), list(_midi[3]))


def flush_ctrl(buf, chars):
    FLG, CTRL, DURA = 0,1,2
    # z>>> : from z to 0 in 4 steps
    # z<<a : from z to a in 4 steps
    # <<<a : from 0 to a in 4 steps
    # <<a> : from 0 to a in 3 steps and to 0 in a step # but not yet.
    
    midi = []
    head = buf[0]
    tail = buf[len(buf)-1]
    if head[FLG] == "<":
        if tail[FLG] == ">":
            bgn = chars[head[CTRL]]
            time = head[DURA]
            topIdx = -1
            for i in range(1, len(buf)):
                elt = buf[i]
                if elt[FLG] == "1":
                    topIdx = i
                    end = chars[elt[CTRL]]
                    midi.append(("1", bgn, end, "%f" % time))
                    for _ in range(0, topIdx-1):
                        midi.append(("0","0","0","0"))
                    bgn = end
                    time = elt[DURA]
                else:
                    time += elt[DURA]
            end = "0"
            midi.append(("1", bgn, end, "%f" % time))

            for _ in range(len(buf) - topIdx):
                midi.append(("0","0","0","0"))
            return midi
        else:
            
            bgn = "0"
            end = chars[tail[CTRL]]
            time = sum(elt[DURA] for elt in buf)
            midi.append(("1", bgn, end, "%f" % time))
    elif head[FLG] == "-":
        midi.append(("0","0","0","0"))
    else:
        if tail[FLG] == "<":
            bgn = chars[head[CTRL]]
            end = "0"
            time = sum(elt[DURA] for elt in buf)
            midi.append(("1", bgn, end, "%f" % time))
        elif tail[FLG] == ">":
            bgn = chars[head[CTRL]]
            end = "0"
            time = sum(elt[DURA] for elt in buf)
            midi.append(("1", bgn, end, "%f" % time))
            
        elif tail[FLG] == "=":
            bgn = chars[head[CTRL]]
            end = chars[head[CTRL]]
            time = sum(elt[DURA] for elt in buf)
            midi.append(("1", bgn, end, "%f" % time))
            
        else:
            bgn = chars[head[CTRL]]
            end = chars[tail[CTRL]]
            time = sum(elt[DURA] for elt in buf)
            midi.append(("1", bgn, end, "%f" % time))
        
    for _ in range(len(buf) -1):
        midi.append(("0","0","0","0"))        

    return midi
                    

def parse_bend(steps, chars):
    BPM,UNIT,BEND = 0,1,2
    # bend:
    assert len(steps) > 0, "no step."
    midi = []
    buf = []
    
    for i, step in enumerate(steps):
        bend = step[BEND]
        if bend == "<":
            # hold
            duration = 60 * 1000 / float(step[BPM]) * 4 / float(step[UNIT])
            buf.append(("<", "0", duration))
        elif bend == "-":
            # set default
            if len(buf) > 0:
                midi.extend(flush_bend(buf, chars))
                buf = []
            
            buf.append(("-", "0", 0))
        else:
            if len(buf) > 0:
                if buf[0][0] == "-":
                    midi.extend(flush_bend(buf, chars))
                    buf = []
                    duration = 60 * 1000 / float(step[BPM]) * 4 / float(step[UNIT])
                    buf.append(("1", bend, duration))
                else:
                    if buf[0][1] == bend:
                        # flush buffer and restart save.
                        midi.extend(flush_bend(buf, chars))
                        buf = []
                        duration = 60 * 1000 / float(step[BPM]) * 4 / float(step[UNIT])
                        buf.append(("1", bend, duration))
                    else:
                        # save data and flush buffer
                        duration = 60 * 1000 / float(step[BPM]) * 4 / float(step[UNIT])
                        buf.append(("0", bend, duration))
                        midi.extend(flush_bend(buf, chars))
                        buf = []
            else:
                duration = 60 * 1000 / float(step[BPM]) * 4 / float(step[UNIT])
                buf.append(("1", bend, duration))
    
    if len(buf) > 0:
        midi.extend(flush_bend(buf, chars))
        buf = []
        
    _midi = list(zip(*midi))
    return (list(_midi[0]), list(_midi[1]), list(_midi[2]), list(_midi[3]))



def flush_bend(buf, chars):
    FLG, BEND, DURA = 0,1,2
    # z<<< : from z to 0 in 4 steps
    # z<<a : from z to a in 4 steps
    # <<<a : from 0 to a in 4 steps
    
    midi = []
    head = buf[0]
    tail = buf[len(buf)-1]
    if head[FLG] == "<":
        bgn = "0"
        end = chars[tail[BEND]]
        time = sum(elt[DURA] for elt in buf[:-1])
        midi.append(("1", bgn, end, "%f" % time))
    elif head[FLG] == "-":
        midi.append(("0","0","0","0"))
    else:
        if tail[FLG] == "<":
            bgn = chars[head[BEND]]
            end = "0"
            time = sum(elt[DURA] for elt in buf[:-1])
            midi.append(("1", bgn, end, "%f" % time))
        else:
            bgn = chars[head[BEND]]
            end = chars[tail[BEND]]
            time = sum(elt[DURA] for elt in buf[:-1])
            midi.append(("1", bgn, end, "%f" % time))
        
    for _ in range(len(buf) -1):
        midi.append(("0","0","0","0"))
    return midi


def adjust(lst):
    assert len(lst) > 0, "empty list"

    prev = lst[0]
    ret = [prev]
    for i in range(1, len(lst)):
        curr = lst[i]
        if curr == "0":
            ret.append(prev)
        else:
            ret.append(curr)
            prev = curr
    return ret

class Score(object):
    def __init__(self):
        self.configure = None
        self.patterns = {}
        self.subsongs = {}
        self.contents = []

    def append_pattern(self, pattern):
        self.patterns[pattern.name] = pattern

    def append_subsong(self, subsong):
        self.subsongs[subsong.name] = subsong
        
    def make_content(self, name):
        if name in self.patterns:
            self.contents.extend(self.patterns[name].data)
        else:
            if name in self.subsongs:
                for pattern in self.subsongs[name].patterns:
                    self.contents.extend(pattern.data)
    
    def print_contents(self):
        text = ""
        for content in self.contents:
            try: 
                text += " ".join(content) + "\n"
            except Exception as e:
                print(e)
                print(content)
                raise e
                
            #text += " ".join("%f" % c for c in content) + "\n"
        return text



class Configure(object):
    def __init__(self):
        self.bpm = 0
        self.parts = []
        self.chars = []
        self.notes = []
        self.volumes = []
        self.bend_depths = []
        self.modulations = []
        self.articulations = []
        
    @staticmethod
    def new(lines):
        configure = Configure()
        for line in lines:
            line = line.strip()
            if len(line) <= 0:
                continue
            else:
                if line.startswith("#"):
                    continue
                else:
                    name, _, value = line.partition("=")
                    
                    if name == "bpm":
                        configure.bpm = float(value)
                    elif name == "parts":
                        configure.parts = parse_list(value, str)
                    elif name == "chars":
                        configure.chars = parse_dict(value, str)
                    elif name == "notes":
                        configure.notes = parse_dict(value, str)
                    elif name == "volumes":
                        configure.volumes = parse_dict(value, str)
                    elif name == "bend_depths":
                        configure.bend_depths = parse_dict(value, str)
                    elif name == "modulations":
                        configure.modulations = parse_dict(value, str)
                    elif name == "articulations":
                        configure.articulations = parse_dict(value, str)
                    else:
                        pass
        return configure

class Pattern(object):
    def __init__(self, configure):
        self.configure = configure
        self.name = ""
        self.parts = []
        self.data = []
        self.step_count = 0
        
    @staticmethod
    def new(lines, configure):
        pattern = Pattern(configure)
        steps = []
        for line in lines:
            line = line.strip()
            if len(line) <= 0:
                continue
            else:
                if line.startswith("#"):
                    if line.startswith("#?"):
                        pattern.name, _, _pattern_configure = line[len("#?"):].partition(";")
                        print("now parcing..:%s." % pattern.name)
                        pattern_configure = parse_dict(_pattern_configure, str)
                        pattern.unit = configure.chars[pattern_configure["unit"]]
                        pattern.parts = parse_list(pattern_configure["parts"],str)
                    else:
                        pass
                else:
                    steps.append([c for c in list(line) if c not in ("[", "]", "|", " ", "\misc")]  )
                    
        if len(steps) <= 0:
            assert False, "Empty pattern."
        
        pattern.step_count = len(steps[0])
        
        work = {}
        
        for part in configure.parts:
            if part in pattern.parts:
                index = pattern.parts.index(part)
                _step = steps[index]
                
                if part.startswith("note"):
                    step = [c for c in _step]
                elif part.startswith("bend"):
                    step = [c for c in _step]
                elif part.startswith("modu"):
                    step = [c for c in _step]
                elif part.startswith("vibr"):
                    step = [c for c in _step]
                elif part.startswith("damp"):
                    step = [c for c in _step]
                elif part.startswith("velo"):
                    step = [c for c in _step]
                else:
                    step = [configure.chars[c] for c in _step]
                work[part] = step
            else:
                # undefined part
                if part == "bpm":
                    step = ["%f" % configure.bpm]
                    step.extend(["0" for _ in range(pattern.step_count - 1)])
                elif part == "unit":
                    step = [pattern.unit]
                    step.extend(["0" for _ in range(pattern.step_count - 1)])
                elif part.startswith("note"):
                    step = ["-" for _ in range(pattern.step_count)]
                elif part.startswith("bend"):
                    step = ["-" for _ in range(pattern.step_count)]
                elif part.startswith("modu"):
                    step = ["-" for _ in range(pattern.step_count)]
                elif part.startswith("arti"):
                    step = ["-" for _ in range(pattern.step_count)]
                elif part.startswith("vibr"):
                    step = ["-" for _ in range(pattern.step_count)]
                elif part.startswith("damp"):
                    step = ["-" for _ in range(pattern.step_count)]
                elif part.startswith("velo"):
                    step = ["-" for _ in range(pattern.step_count)]
                else:
                    step = ["0" for _ in range(pattern.step_count)]
                work[part] = step

        for _misc in ("temp%d", "arti%d", "velo%d"):
            for nbr in range(1, 10):
                misc = _misc % nbr
                if misc in pattern.parts:
                    index = pattern.parts.index(misc)
                    _step = steps[index]
                    work[misc] = _step
                else:
                    work[misc] = ["-" for _ in range(pattern.step_count)]
            

        # synthesizer controller
        _bpm, _unit = adjust(work["bpm"]), adjust(work["unit"])


        data = {}
        #for nbr in range(1, 5):
        for nbr in range(1, 10):
            note = parse_note(list(zip(_bpm, _unit, work["note%d" % nbr], work["temp%d" % nbr], work["velo%d" % nbr], work["arti%d" % nbr])), configure.notes, configure.volumes, configure.articulations)
            data["note%d" % nbr] = note

        # bendとモジュレーションは、note1とnote2のみ対応
        for nbr in range(1, 3):
            bend = parse_bend(list(zip(_bpm, _unit, work["bend%d" % nbr])), configure.bend_depths)
            data["bend%d" % nbr] = bend

            modu = parse_ctrl(list(zip(_bpm, _unit, work["modu%d" % nbr])), configure.modulations)
            data["modu%d" % nbr] = modu

        # vibration is channel:1 only(MS-20 only can process the vibration signal.)
        vibr1 = parse_ctrl(list(zip(_bpm, _unit, work["vibr1"])), configure.modulations)
        data["vibr1"] = vibr1
        
        damp = parse_ctrl(list(zip(_bpm, _unit, work["damp"])), configure.modulations)
        data["damp"] = damp
        
        rawdata = []
        for part in configure.parts:
            if part[:4] in ("note", "bend", "modu", "vibr","damp"):
                for elt in data.get(part):
                    rawdata.append(elt)
            else:
                rawdata.append(work[part])

        pattern.data = list(zip(*rawdata))
        
        return pattern
        
class SubSong(object):
    def __init__(self):
        self.name = ""
        self.patterns = []
    
    @staticmethod
    def new(line, score):
        subsong = SubSong()
        lst =  parse_list(line, lambda elt: elt.strip())
        subsong.name = lst[0][len("#$"):]
        for elt in lst[1:]:
            if "*" in elt:
                name, _, times = elt.partition("*")
                name = name.strip()
                if name in score.patterns:
                    for _ in range(int(times.strip())):
                        subsong.patterns.append(score.patterns[name])
                elif name in score.subsongs:
                    for _ in range(int(times.strip())):
                        subsong.patterns.extend(score.subsongs[name])
                else:
                    assert False, "undefined pattern.[%s]" % name
            else:
                if elt in score.patterns:
                    subsong.patterns.append(score.patterns[elt])
                elif elt in score.subsongs:
                    subsong.patterns.extend(score.subsongs[elt])
                else:
                    assert False, "undefined pattern.[%s]" % elt

        return subsong

        
def parse_score(lines):
    score = Score()
    buf = []
    index = 0
    while True:
        if index >= len(lines):
            break
        line = lines[index].strip()
        if len(line) <= 0:
            pass
        elif line.startswith("#config;"):
            index += 1
            while True:
                if index >= len(lines):
                    break
                line = lines[index].strip()
                if line == "#end;":
                    score.configure = Configure.new(buf)
                    buf = []
                    break
                else:
                    buf.append(line)
                    index += 1
        elif line.startswith("#?"):
            buf.append(line)
            index += 1
            while True:
                if index >= len(lines):
                    break
                line = lines[index].strip()
                if line == "#end;":
                    score.append_pattern(Pattern.new(buf, score.configure))
                    buf = []
                    break
                else:
                    buf.append(line)
                    index += 1
        elif line.startswith("#$"):
            # subsong
            score.append_subsong(SubSong.new(line, score))
        elif line.startswith("#!"):
            name = line[len("#!"):]
            score.make_content(name)
        else:
            pass
            
        index += 1
    return score      

import os, sys
if __name__ == '__main__':
    # scoredir = r"C:\Users\takatoshi\Music\paperdrumer2\paperdrumer2\score2"
    scoredir = r"F:\_src\paperdrumer2\score2"
    argv = sys.argv
    
    if len(argv) < 2:
        print("usage: python %s scorename [...]" % os.path.basename(__file__))
    else:
        for arg in argv[1:]:
            with open(os.path.join(scoredir, "%s_score2.txt" % arg), "r") as infile, \
                 open(os.path.join(scoredir, "%s_data2.txt" % arg), "w") as outfile:
                print("--begin parcing score file: %s_score2.txt" % arg)
                lines = infile.readlines()
                score = parse_score(lines)

                outfile.write(score.print_contents())

        print("end;")
        
        
        
        
"""
C:/Users/takatoshi/Music/pd/mysample
C:/Users/takatoshi/Desktop/paperdrumer/wav
C:/Users/takatoshi/Music/paperdrumer_0_2/scoreex
C:/Users/takatoshi/Music/paperdrumer_0_2/sample
C:/Users/takatoshi/Music/paperdrumer_0_2/newsample
C:/Users/takatoshi/Music/sugy
C:/Users/takatoshi/Music/basseq/data
C:/Users/takatoshi/Music/paperdrumer_0_2/score3
C:/Users/takatoshi/Music/paperdrumer_0_2/score4
"""