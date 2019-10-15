import contextlib
import mwviews.api
import requests
import signal

# Code Below taken from https://www.jujens.eu/ (with minor modification)
#-------------------------------------------------------------------------------
@contextlib.contextmanager
def timeout(time):
    # Register a function to raise a TimeoutError on the signal.
    signal.signal(signal.SIGALRM, raise_timeout)
    # Schedule the signal to be sent after ``time``.
    signal.alarm(time)

    try:
        yield
    except TimeoutError:
        pass
    finally:
        # Unregister the signal so it won't be triggered
        # if the timeout is not reached.
        signal.signal(signal.SIGALRM, signal.SIG_IGN)


def raise_timeout(signum, frame):
    raise TimeoutError
#-------------------------------------------------------------------------------
# Code Above taken from https://www.jujens.eu/

def get_list_of_trans_people():
    result = {}
    s = requests.session()
    api_url = "https://en.wikipedia.org/w/api.php"
    categories = [
        "Category:Transgender_and_transsexual_women",
        "Category:Transgender_and_transsexual_men",
        "Category:People_with_non-binary_gender_identities"
    ]
    parameters = [{
        "action": "query",
        "cmtitle": category,
        "list": "categorymembers",
        "cmlimit":"max",
        "format": "json"
    } for category in categories]
    excluded = [
        'List of people with non-binary gender identities',
        'List of non-binary writers',
        'Trans man'
    ]
    for parameter in parameters:
        r = s.get(url=api_url, params=parameter)
        data = r.json()
        for page in data['query']['categorymembers']:
            if page['ns'] == 0:
                name = page['title']
                id = page['pageid']
                if id not in result:
                    if name not in excluded:
                        result[id] = name
    return list(result.values())

def get_views(article, client):
    views = 0
    try:
        with timeout(10):
            result = client.article_views("en.wikipedia", article, granularity='monthly', start="20000101")
    except Exception as e:
        print(e)
        return None
    for value in result.values():
        assert len(value) == 1
        for view in value.values():
            if view is not None:
                views += view
    return views

def write_unsorted_data():
    client = mwviews.api.PageviewsClient("chansel")
    ppl = get_list_of_trans_people()
    with open('unsorted_data.txt', 'w') as f:
        for person in ppl:
            f.write(person + ' ' + str(get_views(person, client)) + '\n')
            f.flush()

def write_sorted_data():
    values = {}
    with open('unsorted_data.txt', 'r') as f:
        for line in f:
            split = line.split()
            name = ' '.join(split[:-1])
            value = None if split[-1] == 'None' else int(split[-1])
            values[name] = value
    nonnull_values = values.copy()
    null_keys = []
    for key, value in nonnull_values.items():
        if value is None:
            null_keys.append(key)
    for key in null_keys:
        del nonnull_values[key]
    null_values = {key: values[key] for key in null_keys}
    max_width = max([len(key) for key in nonnull_values.keys()])
    with open('sorted_data.txt', 'w') as f:
        for key, value in sorted(nonnull_values.items(), key=lambda item: item[1], reverse=True):
            f.write(f"{key:<{max_width}} {value:,}\n")
        for key, value in null_values.items():
            f.write(f"{key:<{max_width}} N/A\n")

write_unsorted_data()
write_sorted_data()
