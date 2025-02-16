/**
 * @typedef MenuItem
 * @type {object}
 * @property {(string|null)} id
 * @property {(string|null)} icon
 * @property {string} label
 * @property {(string|null)} page
 * @property {(Array.<MenuItem>|null)} items
 *
 * @typedef Version
 * @type {object}
 * @property {string} current
 * @property {string} latest
 * @property {string} schema
 *
 * @typedef Menu
 * @type {object}
 * @property {Array.<MenuItem>} items
 * @property {Version} version
 *
 * @typedef Project
 * @type {object}
 * @property {string} code
 * @property {string} name
 *
 * @typedef Properties
 * @type {object}
 * @property {Menu} menu
 * @property {string} project
 * @property {string} username
 * @property {string} current_page
 * @property {string} logout_path
 */
const van = window.top.van;
const { a, button, div, i, img, label, option, select, span } = van.tags;

const Sidebar = (/** @type {Properties} */ props) => {
    if (Sidebar.StreamlitInstance) {
        Sidebar.StreamlitInstance.setFrameHeight(1);
    }

    if (!window.testgen.loadedStylesheets.sidebar) {
        document.adoptedStyleSheets.push(stylesheet);
        window.testgen.loadedStylesheets.sidebar = true;
    }

    return div(
        {class: 'menu'},
        div(
            { class: 'menu--project' },
            div({ class: 'caption' }, 'Project'),
            div(props.project),
        ),
        () => {
            const menuItems = props.menu?.val.items || [];
            return div(
                {class: 'content'},
                menuItems.map(item =>
                    item.items?.length > 0
                    ? MenuSection(item, props.current_page)
                    : MenuItem(item, props.current_page))
            );
        },
        button(
            { class: `tg-button logout`, onclick: (event) => navigate(event, props.logout_path?.val) },
            i({class: 'material-symbols-rounded'}, 'logout'),
            span('Logout'),
        ),
        span({class: 'menu--username'}, props.username),
        () => Version(props.menu?.val.version),
    );
};

const MenuSection = (/** @type {MenuItem} */ item, /** @type {string} */ currentPage) => {
    return div(
        {class: 'menu--section'},
        div({class: 'menu--section--label'}, item.label),
        div(
            {class: 'menu--section--items'},
            ...item.items.map(child => MenuItem(child, currentPage)),
        )
    );
}

const MenuItem = (/** @type {MenuItem} */ item, /** @type {string} */ currentPage) => {
    const classes = van.derive(() => {
        if (isCurrentPage(item.page, currentPage?.val)) {
            return 'menu--item active';
        }
        return 'menu--item';
    });

    return a(
        {class: classes, href: `/${item.page}`, onclick: (event) => navigate(event, item.page, currentPage?.val)},
        i({class: 'menu--item--icon material-symbols-rounded'}, item.icon),
        span({class: 'menu--item--label'}, item.label),
    );
};

const Version = (/** @type {Version} */ version) => {
    const expanded = van.state(false);

    const icon = van.derive(() => expanded.val ? 'expand_less' : 'expand_more');
    const classes = van.derive(() => expanded.val ? ' version expanded' : 'version');

    return div(
        {class: classes, onclick: () => { expanded.val = !expanded.val; }},
        VersionRow(
            'version',
            version.current,
            i({class: 'material-symbols-rounded version--dropdown-icon'}, icon),
        ),
        div(
            {class: 'version--details'},
            VersionRow('latest version', version.latest),
            VersionRow('schema revision', version.schema),
        ),
    );
};

const VersionRow = (/** @type string */ label, /** @type string */ version, iconEl = undefined) => {
    return div(
        {class: 'version--row'},
        span({class: 'version--row--label'}, `${label}:`),
        span({class: 'version--row--value'}, version),
        iconEl,
    );
};

function navigate(/** @type object */ event, /** @type string */ path, /** @type string */ currentPage = null) {
    // Needed to prevent page refresh
    // Returning false does not work because VanJS does not use inline handlers -> https://github.com/vanjs-org/van/discussions/246
    event.preventDefault();
    // Prevent Streamlit from reacting to event
    event.stopPropagation();

    if (Sidebar.StreamlitInstance && path !== currentPage) {
        Sidebar.StreamlitInstance.sendData(path);
    }
}

function isCurrentPage(/** @type string */ itemPath, /** @type string */ currentPage) {
    const normalizedItemPath = normalizePath(itemPath);
    const normalizedCurrentPagePath = normalizePath(currentPage);
    const isTheSamePage = normalizedItemPath === normalizedCurrentPagePath;
    const isASubPage = normalizedCurrentPagePath.startsWith(`${normalizedItemPath}:`);

    return isTheSamePage || isASubPage;
}

function normalizePath(path) {
    return path || '';
}

const stylesheet = new CSSStyleSheet();
stylesheet.replace(`
.menu {
    position: relative;
    display: flex;
    flex-direction: column;
    height: calc(100% - 76px);
}

.menu > .menu--project {
    padding: 0 20px;
    margin-bottom: 16px;
}

.menu > .menu--username {
    position: absolute;

    left: 0;
    bottom: 0;

    padding-left: 16px;
    padding-bottom: 8px;

    max-width: 35%;
    overflow-x: hidden;
    text-overflow: ellipsis;
    text-wrap: nowrap;

    color: var(--secondary-text-color);
}

.menu > .menu--username:before {
    content: 'User: ';
}

.menu > .content > .menu--section > .menu--section--label {
    padding: 8px 16px;
    font-size: 15px;
    color: var(--disabled-text-color);
}

.menu .menu--item {
    height: 40px;
    display: flex;
    align-items: center;
    padding: 0 16px;
    color: var(--secondary-text-color);
    border-left: 4px solid transparent;
    font-weight: 500;
    text-decoration: unset;
}

.menu .menu--item.active {
    color: var(--primary-color);
    background: var(--sidebar-active-item-color);
    border-left-color: var(--sidebar-active-item-border-color);
}

.menu .menu--item > .menu--item--icon {
    font-size: 20px;
    line-height: 20px;
}

.menu .menu--item > .menu--item--label {
    margin-left: 16px;
}

.menu .menu--item:hover {
    cursor: pointer;
    background: var(--sidebar-item-hover-color);
}

.menu .version {
    color: var(--secondary-text-color);
    display: flex;
    flex-direction: column;
    padding: 8px 16px;
    cursor: pointer;
}

.menu .version .version--dropdown-icon {
    font-size: 19px;
}

.menu .version .version--row {
    display: flex;
    align-items: center;
    justify-content: flex-end;
}

.menu .version .version--row .version--row--label {
    font-weight: 500;
    margin-right: 4px;
}

.menu .version .version--details {
    display: none;
    flex-direction: column;
}

.menu .version .version--details {
    display: none;
    margin-top: 4px;
}

.menu .version.expanded .version--details {
    display: block;
}

.version--row + .version--row {
    margin-top: 4px;
}

.menu > :nth-child(1 of button) {
    margin-top: auto !important;
}

.menu > button {
    margin: 16px;
    color: var(--secondary-text-color) !important;
}

.menu > button.logout {
    margin-top: 8px;
}

.menu > button.users {
    margin-bottom: 0px;
}

/* Intentionally duplicate from button.js */
button.tg-button {
    position: relative;
    overflow: hidden;

    display: flex;
    flex-direction: row;
    align-items: center;
    justify-content: center;

    outline: 0;
    border: unset;
    background: transparent;
    border-radius: 4px;
    padding: 8px 16px;

    color: var(--primary-text-color);
    cursor: pointer;

    font-size: 14px;

    transition: background 400ms;
}

button.tg-button:hover {
    background: rgba(0, 0, 0, 0.04);
}

button.tg-button > i {
    font-size: 18px;
    margin-right: 8px;
}
/* ... */
`);

window.testgen.components.Sidebar = Sidebar;
