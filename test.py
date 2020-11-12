data = [['Name', 'Zeit bis', 'Format', 'Rechnugsstellung', 'Bezahlt', 'Rechnungsnummer', 'Seite'], ['HS Furtwangen', '', '', '', '', 156.0], ['AOK ', '', '', '', 2.0, 81.0], ['Modehaus Kaiser', '', '', '', 3.0, 203.0], ['SICK ', '', '', '', 4.0, 45.0], ['Uni Konstanz', '', '', '', 5.0, 123.0], ['DHBW Lörrach', '', '', '', 6.0, 45.0], ['Fraunhofer', '', '', '', 7.0, 161.0], ['Macromedia ', '', '', '', 8.0, 7.0], ['HTWG Konstanz', '', '', '', 9.0, 81.0]]
print(f'{data}\n\n')

def delete_empty_columns(data):
    indexes = []
    for ri, r in enumerate(data[1:]):
        for ci, c in enumerate(r):
            if c == "" and ri == 0:
                indexes.append(ci)
            elif c != "" and ci in indexes:
                indexes.remove(ci)
    print(indexes)
    for ri, r in enumerate(data):
        for i in sorted(indexes, reverse=True):
            r.pop(i)
    # print(data)
    return data


print(delete_empty_columns(data))
