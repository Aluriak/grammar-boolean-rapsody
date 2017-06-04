import csv
import gbr


def problems(fname:str='data_gbr.tsv'):
    """Read problems from given file, yield complex name and problem definition"""
    with open(fname) as fd:
        for complex, expr in csv.reader(fd, delimiter='\t'):
            yield complex, expr


if __name__ == "__main__":
    for complex, expr in problems():
        print('—' * 80)
        print('Complex:', complex)
        for solution in gbr.compile_input('{}'.format(expr)):
            print('\t' + ' & '.join(solution))

