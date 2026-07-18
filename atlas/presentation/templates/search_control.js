{% macro script(this, kwargs) %}
const atlasMap = {{ this._parent.get_name() }};
const atlasLayerControl = {{ this.layer_control_name }};
const atlasSearchIndex = {{ this.index_json|safe }};
const atlasSearchLabels = Object.keys(atlasSearchIndex);
let atlasSearchMarker = null;
let atlasMatches = [];
let atlasActiveResult = -1;
const AtlasSearchControl = L.Control.extend({
    options: {position: "topleft"},
    onAdd: function () {
        const box = L.DomUtil.create("div", "atlas-search-control");
        const field = L.DomUtil.create("div", "atlas-search-field", box);
        const input = L.DomUtil.create("input", "atlas-search-input", field);
        const clear = L.DomUtil.create("button", "atlas-search-clear", field);
        const results = L.DomUtil.create("div", "atlas-search-results", box);
        input.type = "search";
        input.placeholder = "Cerca nell’atlante…";
        input.setAttribute("aria-label", "Cerca nell’atlante");
        input.setAttribute("autocomplete", "off");
        input.setAttribute("inputmode", "search");
        input.setAttribute("aria-controls", "atlas-search-results");
        input.setAttribute("aria-expanded", "false");
        clear.type = "button";
        clear.textContent = "×";
        clear.setAttribute("aria-label", "Cancella ricerca");
        results.id = "atlas-search-results";
        results.setAttribute("role", "listbox");
        results.hidden = true;

        const hideResults = () => {
            results.hidden = true;
            results.replaceChildren();
            input.setAttribute("aria-expanded", "false");
            atlasActiveResult = -1;
        };
        const focusResult = (label) => {
            if (!label) return;
            const [lat, lon, zoom] = atlasSearchIndex[label];
            atlasMap.setView([lat, lon], zoom, {animate: true});
            if (atlasSearchMarker) atlasMap.removeLayer(atlasSearchMarker);
            atlasSearchMarker = L.circleMarker([lat, lon], {radius: 11, color: "#d5a94e", weight: 4, fill: false})
                .addTo(atlasMap).bindPopup(`<b>${label}</b>`).openPopup();
            input.value = label;
            hideResults();
            input.blur();
        };

        const renderResults = () => {
            const query = input.value.trim().toLocaleLowerCase("it");
            if (!query) {hideResults(); return;}
            atlasMatches = atlasSearchLabels
                .filter((label) => label.toLocaleLowerCase("it").includes(query))
                .sort((a, b) => {
                    const aStarts = a.toLocaleLowerCase("it").split(" · ").pop().startsWith(query) ? 0 : 1;
                    const bStarts = b.toLocaleLowerCase("it").split(" · ").pop().startsWith(query) ? 0 : 1;
                    return aStarts - bStarts || a.localeCompare(b, "it");
                }).slice(0, 6);
            results.replaceChildren();
            atlasMatches.forEach((label) => {
                const [category, ...nameParts] = label.split(" · ");
                const option = document.createElement("button");
                option.type = "button";
                option.className = "atlas-search-result";
                option.setAttribute("role", "option");
                const name = document.createElement("span");
                const kind = document.createElement("small");
                name.textContent = nameParts.join(" · ");
                kind.textContent = category;
                option.append(name, kind);
                option.addEventListener("pointerdown", (event) => {event.preventDefault(); focusResult(label);});
                results.appendChild(option);
            });
            results.hidden = atlasMatches.length === 0;
            input.setAttribute("aria-expanded", atlasMatches.length ? "true" : "false");
            atlasActiveResult = -1;
        };

        const setActive = (nextIndex) => {
            const options = [...results.querySelectorAll(".atlas-search-result")];
            if (!options.length) return;
            atlasActiveResult = (nextIndex + options.length) % options.length;
            options.forEach((option, index) => option.setAttribute("aria-selected", index === atlasActiveResult ? "true" : "false"));
            options[atlasActiveResult].scrollIntoView({block: "nearest"});
        };
        input.addEventListener("input", renderResults);
        input.addEventListener("focus", renderResults);
        input.addEventListener("keydown", (event) => {
            if (event.key === "ArrowDown") {event.preventDefault(); setActive(atlasActiveResult + 1);}
            if (event.key === "ArrowUp") {event.preventDefault(); setActive(atlasActiveResult - 1);}
            if (event.key === "Escape") {event.preventDefault(); hideResults(); input.blur();}
            if (event.key === "Enter") {
                event.preventDefault();
                const label = atlasMatches[atlasActiveResult] || atlasMatches[0];
                focusResult(label);
            }
        });
        clear.addEventListener("click", () => {
            input.value = "";
            if (atlasSearchMarker) {atlasMap.removeLayer(atlasSearchMarker); atlasSearchMarker = null;}
            hideResults();
            input.focus();
        });
        atlasMap.on("click", hideResults);
        L.DomEvent.disableClickPropagation(box);
        L.DomEvent.disableScrollPropagation(box);
        return box;
    }
});
new AtlasSearchControl().addTo(atlasMap);

const updateAtlasControls = () => {
    const touchLayout = L.Browser.touch || window.matchMedia("(hover: none) and (pointer: coarse)").matches;
    const roomyDesktop = !touchLayout && window.matchMedia("(min-width: 1025px) and (min-height: 700px)").matches;
    if (roomyDesktop) atlasLayerControl.expand();
    else atlasLayerControl.collapse();
};
updateAtlasControls();
window.addEventListener("resize", updateAtlasControls, {passive: true});
{% endmacro %}
