import re

def match_a_followed_by_b(s):
    return bool(re.fullmatch(r"ab*", s))


def match_a_two_three_b(s):
    return bool(re.fullmatch(r"ab{2,3}", s))


def find_snake_case_words(s):
    return re.findall(r"\b[a-z]+(?:_[a-z]+)+\b", s)

def find_capitalized_words(s):
    return re.findall(r"\b[A-Z][a-z]+\b", s)

def match_a_to_b(s):
    return bool(re.fullmatch(r"a.*b", s))

def replace_separators_with_colon(s):
    return re.sub(r"[ ,\.]+", ":", s)

def snake_to_camel(s):
    parts = s.strip("_").split("_")
    if not parts or parts == [""]:
        return ""
    return parts[0].lower() + "".join(p[:1].upper() + p[1:].lower() for p in parts[1:] if p)

def split_by_uppercase(s):
    return [x for x in re.split(r"(?=[A-Z])", s) if x]

def insert_spaces_before_capitals(s):
    return re.sub(r"(?<!^)(?=[A-Z])", " ", s).strip()

def convert_to_snake_case(s):
    s = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", s)
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
    return s.lower()


if __name__ == "__main__":
    tests = {
        "1": ["a", "ab", "abbb", "ac"],
        "2": ["abb", "abbb", "abbbb", "a"],
        "3": ["abc_def", "a_b_c", "ABC_def", "nope"],
        "4": ["Apple", "Xy", "USA", "aBc"],
        "5": ["ab", "a---b", "ac", "ba"],
        "6": ["hello, world. ok", "a b,c...d"],
        "7": ["snake_case_string", "_hello__world_"],
        "8": ["SplitThisStringABC", "helloWorld"],
        "9": ["InsertSpacesHereNow", "NASAProjectX"],
        "10": ["camelCaseString", "PascalCaseString", "HTTPServerError"],
    }

    print("ex1:", [match_a_followed_by_b(x) for x in tests["1"]])
    print("ex2:", [match_a_two_three_b(x) for x in tests["2"]])
    print("ex3:", [find_snake_case_words(x) for x in tests["3"]])
    print("ex4:", [find_capitalized_words(x) for x in tests["4"]])
    print("ex5:", [match_a_to_b(x) for x in tests["5"]])
    print("ex6:", [replace_separators_with_colon(x) for x in tests["6"]])
    print("ex7:", [snake_to_camel(x) for x in tests["7"]])
    print("ex8:", [split_by_uppercase(x) for x in tests["8"]])
    print("ex9:", [insert_spaces_before_capitals(x) for x in tests["9"]])
    print("ex10:", [convert_to_snake_case(x) for x in tests["10"]])