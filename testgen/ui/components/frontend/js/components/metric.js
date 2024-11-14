/**
 * @typedef Properties
 * @type {object}
 * @property {number} value
 * @property {number?} delta
 */
import van from '../van.min.js';
import { getValue, loadStylesheet } from '../utils.js';

const { i, div, span } = van.tags;

const Metric = function(/** @type Properties */props) {
    loadStylesheet('metric', stylesheet);

    const deltaIcon = van.derive(() => getValue(props.delta) >= 0 ? 'arrow_upward' : 'arrow_downward');
    const deltaColor = van.derive(() => getValue(props.delta) >= 0 ? 'rgb(9, 171, 59)' : 'rgb(255, 43, 43)');

    return div(
        { class: 'flex-column fx-align-flex-center' },
        span(
            { style: 'font-size: 36px;' },
            props.value,
        ),
        () => getValue(props.delta)
            ? div(
                { class: 'flex-row', style: () => `color: ${getValue(deltaColor)};` },
                i(
                    {class: 'material-symbols-rounded', style: 'font-size: 20px;'},
                    deltaIcon,
                ),
                span(props.delta),
            )
            : undefined,
    );
}

const stylesheet = new CSSStyleSheet();
stylesheet.replace(``);

export { Metric };
