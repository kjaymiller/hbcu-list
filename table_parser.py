import pathlib
from string import Template

import pandas as pd
from slugify import slugify


df = pd.read_csv('Most-Recent-Cohorts-All-Data-Elements.csv', usecols=['INSTNM','INSTURL'])
df['INSTURL'] = df['INSTURL'].str.rstrip('/')
df['slug'] = df.apply(lambda x: slugify(x['INSTNM']), axis=1)

base_hbcus = pd.read_html("HBCU_LIST.html")[0]
base_hbcus['slug'] = base_hbcus.apply(lambda x: slugify(x['School']), axis=1)

hbcus = pd.merge(base_hbcus, df, on='slug')
hbcus.rename(columns={"Regionally accredited[3]": "Regionally Accredited"}, inplace=True)

def _gen_slug_link(school):
    """create markdown link to associated pages object"""

    return f"[{school.School}](/pages/{school.slug}.md) - {school.INSTURL}"


def gen_readme():
    """build readme with readme_templates"""
    hbcus['readme'] = hbcus.apply(_gen_slug_link, axis=1)

    states_list = []

    for name in sorted(hbcus["State/Territory"].unique()):
        schools = hbcus[hbcus["State/Territory"] == name]['readme'].values
        schools = "\n\n".join(schools)
        state_section = f"## {name}\n{schools}"
        states_list.append(state_section)

    state_sections = "\n\n".join(states_list)

    with open("README.md", "w") as fp:
        fp.write(f"""# HBCUs in the the United States
{state_sections}

#### source: 
- [Wikipedia List of HBCUs](https://en.wikipedia.org/wiki/List_of_historically_black_colleges_and_universities)
- [College Scorecard US Dept. of Education](https://data.ed.gov/dataset/college-scorecard-all-data-files-through-6-2020/resources?resource=823ac095-bdfc-41b0-b508-4e8fc3110082)
#### license: [MIT License](/LICENSE)""")


def build_pages():
    hbcus.set_index("School")
    hbcu_json = hbcus.to_dict(orient="records")

    for row in hbcu_json:
        f_meta = []

        for name, val in row.items():
            if name != "Comment":
                f_meta.append(f"{name}: {val}")

        ftext = "\n".join(f_meta)

        filepath = pathlib.Path(slugify(row["School"])).with_suffix(".md")
        page = pathlib.Path("pages").joinpath(filepath)

        page.write_text(
            f"""---
{ftext}
---
{row['Comment']}"""
        )


if __name__ == "__main__":
    gen_readme()
