from yargy.interpretation import fact
from yargy import rule, Parser, or_, not_, and_
from yargy.predicates import eq, type
from yargy.pipelines import morph_pipeline
import re

def yargy_parser(path):
    RULE = fact (
        'RULE',
        ['name','tresh','num']
    )

    INT = type('INT')
    PUNCT = type('PUNCT')

    DOT = or_(eq('.'),eq(','))


    NAME_mtbf = morph_pipeline(
            [
                'MTBF',
                'mean time between',
                'mean time between failures',
                'mean time between failure',
            ]
        ).interpretation(
        RULE.name
    )

    NAME_mttr = morph_pipeline(
            [
                'MTTR',
                'mean time to',
                'Mean Time To Repair',
                'repair time',
            ]

    ).interpretation(
        RULE.name
    )


    NUM_MTBF = or_(rule(INT, DOT, INT), rule(INT), rule(INT, DOT, INT, DOT, INT))

    UNIT_mtbf = morph_pipeline(
            [
                '年',
                'year',
                'years',
                'hour',
                'hours',
                'год',
                'час',
                'h',
                '小时'
            ]
        )

    UNIT_mttr  = morph_pipeline(
            [
                'hour',
                'hours',
                'час',
                'h',
                '小时'
            ]
        )


    X_mtbf = rule(NUM_MTBF, UNIT_mtbf.optional()).interpretation(
        RULE.num
    )

    X_mttr = rule(INT, UNIT_mttr.optional()).interpretation(
        RULE.num
    )

    TRESH = rule(and_(not_(eq(NUM_MTBF)),or_(not_(eq(NAME_mttr)),not_(eq(NAME_mtbf))),not_(eq(UNIT_mtbf)), not_(eq(DOT)),
                 not_(eq(INT)) , not_(eq(X_mttr)), not_(eq(X_mtbf)))).interpretation(
        RULE.tresh
    )

    rule_1 = (rule(NAME_mtbf ,(TRESH.optional()).repeatable(),  X_mtbf).repeatable()
             ).interpretation(
        RULE
    )

    rule_2 = (rule(NAME_mttr ,(TRESH.optional()).repeatable(),  X_mttr).repeatable()
             ).interpretation(
        RULE
    )
    f = open(path, 'r')
    text = f.read()
    #Remove line separators
    text = re.sub("^\s+|\n|\r|\s+$", '', text)
    line = text
    #Temporary workaround. Fix it to site by site processing later
    n = 500
    text = [line[i-5 if i-5>0 else 0:i+n+5 if i+n+5 < len(line) else len(line) -1] for i in range(0, len(line), n)]
    MEASURE = rule(or_(NAME_mtbf, X_mtbf, NAME_mttr, X_mttr))
    new_line = []
    #Parser #1 text preprocessing
    parser = Parser(MEASURE)
    for line in text:
        matches = list(parser.findall(line))
        spans = [_.span for _ in matches]
        new_span = [0,0]
        if spans != [] and len(spans)>=2:
            for i in range(0,len(spans)-1,1):
                mini = 1000000
                maxi = 0
                if spans[i][0] < mini:
                    new_span[0] = spans[i][0]
                    mini = spans[i][0]
                if spans[i+1][1] > maxi:
                    new_span[1] = spans[i+1][1]
                    maxi = spans[i+1][1]
                for i in range(new_span[0],new_span[1]):
                    new_line.append(line[i])
                new_line.append(' \n ')
    new_line = ''.join(new_line)
    new_line = new_line.split('\n')
    LIST = []
    MEASURE = or_(rule_1,rule_2).interpretation(
        RULE
    )
    #Parser #2 Parsing reliability metrics.
    parser = Parser(MEASURE)
    for line in new_line:
        matches = list(parser.findall(line))
        spans = [_.span for _ in matches]
        if spans != []:
            if matches:
                for match in matches:
                    LIST.append(match.fact)
    return LIST

def finding_num(b):
    names_mtbf = ['mtbf',
                'mean time between',
                'mean time between failures',
                'mean time between failure',]
    names_mttr = ['mttr',
                'mean time to',
                'mean time to repair',
                'mean time to repairs',
                 'repair time']
    dict_num = {'MTTR':{},'MTBF':{}}
    dict_max = {'MTTR':0,'MTBF':0}
    for i in range(len(b)):
        print(i)
        if b[i].name.lower() in names_mtbf:
            b[i].name = 'MTBF'
        elif b[i].name.lower() in names_mttr:
            b[i].name = 'MTTR'
        if ('years' or 'year' or '年' or 'год') in b[i].num:
            num = float((b[i].num).split(' ')[0])
            num = num * 8760
            b[i].num = str(int(round(num))) + str(' ') + str('hours')
        else:
            b[i].num = str(int(float(((b[i].num).replace(',','')).split(' ')[0]))) + str(' ') + str('hours')
        num = int((b[i].num).split(' ')[0])
        print(b[i].name,b[i].num)
        try:
            dict_num[b[i].name][num] += 1
        except:
            dict_num[b[i].name][num] = 1
    print(dict_num)
    #Matching value is the most repeatable one.
    for name in dict_num:
        for num in dict_num[name]:
            if dict_num[name][num] > dict_max[name]:
                dict_max[name] = num
    return dict_max
