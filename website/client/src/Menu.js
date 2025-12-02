import { Button, Menu, MenuItem } from "@mui/material"
import { useState } from "react"

const MenuComponent = ({title, values, handleSelect}) => {
    const [anchorEl, setAnchorEl] = useState(null);
    const open = Boolean(anchorEl);
    const handleClick = (event) => {
        setAnchorEl(event.currentTarget);
    };
    const handleClose = (value) => {
        if (typeof(value) == 'string') {
            handleSelect(value)
        }
        setAnchorEl(null);
    };

    return (
        <div>
            <Button
                id="basic-button"
                aria-controls={open ? 'basic-menu' : undefined}
                aria-haspopup="true"
                aria-expanded={open ? 'true' : undefined}
                onClick={handleClick}
            >
                {title}
            </Button>
            <Menu
                id="basic-menu"
                anchorEl={anchorEl}
                open={open}
                onClose={handleClose}
                slotProps={{
                    list: {
                        'aria-labelledby': 'basic-button',
                    },
                }}
            >
                {values.map((item) => {
                    return (
                        <MenuItem onClick={() => handleClose(item)}>{item}</MenuItem>
                    )
                })}
            </Menu>
        </div>
    )
}

export default MenuComponent