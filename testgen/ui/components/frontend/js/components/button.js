/**
 * @typedef Properties
 * @type {object}
 * @property {(string)} type
 * @property {(string|null)} label
 * @property {(string|null)} icon
 * @property {(string|null)} tooltip
 * @property {(string|null)} tooltipPosition
 * @property {(Function|null)} onclick
 * @property {(bool)} disabled
 * @property {string?} style
 */
import { emitEvent, enforceElementWidth, loadStylesheet } from '../utils.js';
import van from '../van.min.js';
import { Streamlit } from '../streamlit.js';

const { button, i, span } = van.tags;
const BUTTON_TYPE = {
    BASIC: 'basic',
    FLAT: 'flat',
    ICON: 'icon',
    STROKED: 'stroked',
};

const Button = (/** @type Properties */ props) => {
    loadStylesheet('button', stylesheet);

    const isIconOnly = props.type === BUTTON_TYPE.ICON || (props.icon?.val && !props.label?.val);
    
    if (!window.testgen.isPage) {
        Streamlit.setFrameHeight(40);
        if (isIconOnly) { // Force a 40px width for the parent iframe & handle window resizing
            enforceElementWidth(window.frameElement, 40);
        }
    }

    if (props.tooltip) {
        window.frameElement.parentElement.setAttribute('data-tooltip', props.tooltip.val);
        window.frameElement.parentElement.setAttribute('data-tooltip-position', props.tooltipPosition.val);
    }

    const onClickHandler = props.onclick || (() => emitEvent('ButtonClicked'));
    return button(
        {
            class: `tg-button tg-${props.type.val}-button ${props.type.val !== 'icon' && isIconOnly ? 'tg-icon-button' : ''}`,
            style: props.style?.val,
            onclick: onClickHandler,
            disabled: !!props.disabled?.val,
        },
        span({class: 'tg-button-focus-state-indicator'}, ''),
        props.icon ? i({class: 'material-symbols-rounded'}, props.icon) : undefined,
        !isIconOnly ? span(props.label) : undefined,
    );
};

const stylesheet = new CSSStyleSheet();
stylesheet.replace(`
button.tg-button {
    width: 100%;
    height: 40px;

    position: relative;
    overflow: hidden;

    display: flex;
    flex-direction: row;
    align-items: center;
    justify-content: center;

    outline: 0;
    border: unset;
    border-radius: 4px;
    padding: 8px 11px;

    cursor: pointer;

    font-size: 14px;
    color: var(--button-text-color);
    background: var(--button-basic-background);
}

button.tg-button .tg-button-focus-state-indicator::before {
    content: "";
    opacity: 0;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    position: absolute;
    pointer-events: none;
    border-radius: inherit;
    background: var(--button-hover-state-background);
}

button.tg-button.tg-basic-button {
    color: var(--button-basic-text-color);
}

button.tg-button.tg-flat-button {
    color: var(--button-flat-text-color);
    background: var(--button-flat-background);
}

button.tg-button.tg-stroked-button {
    color: var(--button-stroked-text-color);
    background: var(--button-stroked-background);
    border: var(--button-stroked-border);
}

button.tg-button.tg-icon-button {
    width: 40px;
}

button.tg-button:has(span) {
    padding: 8px 16px;
}

button.tg-button:not(.tg-icon-button):has(span):has(i) {
    padding-left: 8px;
}

button.tg-button[disabled] {
    color: var(--disabled-text-color);
    cursor: not-allowed;
}

button.tg-button.tg-icon-button > i {
    font-size: 18px;
}

button.tg-button > i:has(+ span) {
    margin-right: 8px;
}

button.tg-button:hover:not([disabled]) .tg-button-focus-state-indicator::before {
    opacity: var(--button-hover-state-opacity);
}
`);

export { Button };
