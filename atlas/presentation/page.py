from __future__ import annotations

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from streamlit_folium import st_folium

from atlas.core.engine import MapEngine


class PageRenderer:
    def __init__(self, root: Path) -> None:
        self.root = root

    def render(self, engine: MapEngine) -> None:
        st.set_page_config(
            page_title="Atlante geografico per concorsi pubblici",
            page_icon="🧭",
            layout="wide",
            initial_sidebar_state="collapsed",
        )
        css = (self.root / "atlas" / "presentation" / "page.css").read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
        self._inject_webapp_meta()
        st.markdown(
            """<div class='hero'><div><div class='eyebrow'>Concorsi pubblici · Geografia</div>
            <h1>L’atlante per ripassare la geografia.</h1></div>
            <p>Esplora la cartina interattiva e allenati sulle domande di geografia dei concorsi pubblici in Italia:
            Stati europei, regioni, province, capoluoghi, fiumi, laghi e rilievi.</p></div>""",
            unsafe_allow_html=True,
        )
        with st.spinner("Preparo i livelli cartografici…"):
            map_object = engine.build()
        st_folium(
            map_object,
            use_container_width=True,
            height=760,
            returned_objects=[],
            key="atlante-map",
        )
        st.markdown(
            """<p class='map-note'>Dati cartografici: Natural Earth · Openpolis/geojson-italy ·
            OpenStreetMap contributors. Posizioni di etichette e sorgenti ottimizzate per il ripasso.</p>""",
            unsafe_allow_html=True,
        )

    @staticmethod
    def _inject_webapp_meta() -> None:
        components.html("""
        <script>
        (() => {
          const doc = window.parent.document;
          const ensureMeta = (name, content) => {
            let node = doc.head.querySelector(`meta[name="${name}"]`);
            if (!node) { node = doc.createElement("meta"); node.name = name; doc.head.appendChild(node); }
            node.content = content;
          };
          const ensureLink = (rel, href, sizes = "") => {
            let node = doc.head.querySelector(`link[rel="${rel}"]`);
            if (!node) { node = doc.createElement("link"); node.rel = rel; doc.head.appendChild(node); }
            node.href = href;
            if (sizes) node.sizes = sizes;
          };
          ensureMeta("viewport", "width=device-width, initial-scale=1, viewport-fit=cover");
          ensureMeta("theme-color", "#1d6f5f");
          ensureMeta("apple-mobile-web-app-capable", "yes");
          ensureMeta("apple-mobile-web-app-status-bar-style", "default");
          ensureMeta("apple-mobile-web-app-title", "Atlante Concorsi");
          ensureLink("apple-touch-icon", "/app/static/icon-180.png", "180x180");
          ensureLink("manifest", "/app/static/manifest.webmanifest");
        })();
        </script>
        """, height=0, width=0)
