from geopandas import GeoDataFrame
from numpy.lib.function_base import select
import pandas as pd
from pandas.core.frame import DataFrame
from src.settings import DATA_INTERIM_DIR, DATA_RAW_DIR, DATA_PROCESSED_DIR, FILTERS_DIR
from pathlib import Path
from typing import Dict, List
import json

def load_gdf(path: Path, crs="EPSG:4326") -> GeoDataFrame:
    df = pd.read_pickle(path)
    gdf = GeoDataFrame(df, crs="EPSG:4326")
    return gdf

def load_city_tag(city: str, tag: str, split_values=True, filter_values: Dict[str, str] = None) -> GeoDataFrame:
    path = DATA_RAW_DIR.joinpath(city, f"{tag}.pkl")
    if path.exists():
        gdf = load_gdf(path)
        if split_values:
            gdf[tag] = gdf[tag].str.split(';')
            gdf = gdf.explode(tag)
            gdf[tag] = gdf[tag].str.strip()
        gdf = filter_gdf(gdf, tag, filter_values)
        return gdf
    else:
        return None

def load_city_tag_h3(city: str, tag: str, resolution: int, filter_values: Dict[str, str] = None) -> GeoDataFrame:
    path = DATA_INTERIM_DIR.joinpath(city, f"{tag}_{resolution}.pkl")
    if path.exists():
        gdf = load_gdf(path)
        gdf = filter_gdf(gdf, tag, filter_values)
        return gdf
    else:
        return None


def filter_gdf(gdf: GeoDataFrame, tag: str, filter_values: Dict[str, str]) -> GeoDataFrame:
    if filter_values is not None:
        selected_tag_values = set(filter_values[tag])
        gdf = gdf[gdf[tag].isin(selected_tag_values)]
    return gdf


def load_filter(filter_name: str, values_to_drop: Dict[str, List[str]] = None) -> Dict[str, List[str]]:
    filter_file_path = FILTERS_DIR.joinpath(filter_name)
    if filter_file_path.exists() and filter_file_path.is_file():
        with filter_file_path.open(mode='rt') as f:
            filter_values = json.load(f)
            if values_to_drop is not None:
                for key, values in values_to_drop.items():
                    for value in values:
                        filter_values[key].remove(value)
            return filter_values
    else:
        available_filters = [f.name for f in FILTERS_DIR.iterdir() if f.is_file()]
        raise FileNotFoundError(f"Filter {filter_name} not found. Available filters: {available_filters}")


def load_grouped_city(city: str, resolution: int) -> DataFrame:
    city_df_path = DATA_PROCESSED_DIR.joinpath(city).joinpath(f"{resolution}.pkl")
    return pd.read_pickle(city_df_path)


def load_processed_dataset(resolution: int, select_cities: List[str]=None, drop_cities: List[str]=None,
    select_tags: List[str]=None) -> DataFrame:
    dataset_path = DATA_PROCESSED_DIR.joinpath(f"{resolution}.pkl")
    df = pd.read_pickle(dataset_path)
    if select_cities is not None:
        df = df[df['city'].isin(select_cities)]
    if drop_cities is not None:
        df = df[~df['city'].isin(drop_cities)]
    if select_tags is not None:
        df = df[[*df.columns[df.columns.str.startswith(tuple(select_tags))], 'city']]
    df = df[~(df.drop(columns='city') == 0).all(axis=1)]
    return df