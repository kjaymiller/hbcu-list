import os
import json
import pathlib

import eland as ed
import pandas as pd
from elasticsearch import Elasticsearch
from slugify import slugify
from typer import Typer

app = Typer()


column_values = {
        "INSTNM": str,
        "INSTURL": str,
        "CITY": str,
        "ST_FIPS": int,
        "PBI": float,
        "ANNHI": float,
        "TRIBAL": float,
        "AANAPII": float,
        "HSI": float,
        "NANTI": float,
        "HBCU": float,
        "CURROPER": float,
        "LATITUDE": float,
        "LONGITUDE": float,
        "MENONLY": float,
        "WOMENONLY": float,
        "CONTROL": int,
        "RELAFFIL": str,
        "HIGHDEG": str,
    }

def _translate_code(json_file, df_column, if_None: str="Unknown"):
    j_file = json.loads(pathlib.Path(json_file).read_text())
    return lambda x:j_file.get(str(x), if_None)


converter_list = [
         ("RELAFFIL", _translate_code("translations/relaffil.json", "RELAFFIL", if_None="None")),
         ("CONTROL", _translate_code("translations/control.json", "CONTROL")),
         ("ST_FIPS", _translate_code("translations/st_fips.json", "ST_FIPS")),
         ("HIGHDEG", _translate_code("translations/high_deg.json", "HIGHDEG")),
        ]

converters = {x:y for x,y in converter_list} # To return "ST_FIPS": lambda x:st_fips_json.get(str(x), "Unknown"), etc 

base_df = pd.read_csv(
    "base_data/Most-Recent-Cohorts-All-Data-Elements.csv",
    usecols=list(column_values.keys()),
    converters=converters,
    dtype=column_values,
)


base_df.fillna(0, inplace=True)
base_df['location'] = base_df.apply(lambda x:f"{x.LATITUDE}, {x.LONGITUDE}", axis=1)

# Create DATAFRAME FOR ACTIVE HBCUs and PBIs
hbcus = base_df.loc[(base_df.HBCU == 1) & (base_df.CURROPER == 1)]
pbis = base_df.loc[(base_df.PBI == 1) & (base_df.CURROPER == 1)]

def _gen_slug_link(school):
    """create markdown link to associated pages object"""
    return f"[{school.INSTNM}](/pages/{school.slug}.md) - {school.INSTURL}"


@app.command()
def gen_list(
    filename: pathlib.Path = "readme.md", title="HBCUs in the the United States"
):
    """build readme with readme_templates"""

    states = []

    for df in (hbcus, pbis):
        df["readme"] = df.apply(_gen_slug_link, axis=1)

    for name in sorted(df["ST_FIPS"].unique()):
        state_sections = {}

        for df_name, df in (("hbcus", hbcus), ("pbis", pbis)):
            schools = df[df["ST_FIPS"] == name]["readme"].values.tolist()

            if schools:
                schools = "\n\n".join(schools)
            else:
                schools = "None"
            state_sections[df_name] = schools

        state_section = f"""## {name}
### HBCUs
{state_sections['hbcus']}

### PBIs
{state_sections['pbis']}"""

        states.append(state_section)

    states = "\n".join(states)
    filename.write_text(
        f"""# {title}
{states}

---
#### source: 
    - [College Scorecard US Dept. of Education](https://data.ed.gov/dataset/college-scorecard-all-data-files-through-6-2020/resources?resource=823ac095-bdfc-41b0-b508-4e8fc3110082)

#### license: [MIT License](/LICENSE)"""
    )


# Elastic Load Data
client = Elasticsearch(
    cloud_id=os.environ.get("ES_CLOUD_ID"),
    http_auth=(
        os.environ.get("ES_USERNAME"),
        os.environ.get("ES_PASSWORD"),
    ),
)


es_type_overrides = {
        "location": "geo_point",
        }

@app.command()
def load_to_es():
        ed.pandas_to_eland(
            pd_df=base_df,
            es_client=client,
            es_dest_index=f"US_COLLEGES".lower(),
            es_if_exists="replace",
            es_refresh=True,
            use_pandas_index_for_es_ids=False,
            es_type_overrides = es_type_overrides,
        )


@app.command()
def build_pages():  # TODO REMOVE DEPENDENCY ON WIKIPEDIA
    for df in (hbcus, pbis):
        df.drop(columns='CURROPER', inplace=True)
        dfj = df.to_dict(orient="records")

        for row in dfj:
            f_meta = []

            f_name = row.pop('INSTNM')
            filepath = pathlib.Path(slugify(f_name)).with_suffix(".md")
            f_url = row.pop('INSTURL').rstrip('/')

            for name, val in row.items():
                if val in (1.0, 0.0): 
                    if val:
                        f_name += f" {name}" 

                else:
                    f_meta.append(f"**{name}**: {val}")

            f_text = "\n\n".join(f_meta)

            page = pathlib.Path("pages").joinpath(filepath)

            page.write_text(
            f"""# {f_name}
### {f_url}
---
{f_text}"""
        )


if __name__ == "__main__":
    app()
