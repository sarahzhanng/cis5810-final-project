import React, { useState, useRef } from "react";
import { ImageList, ImageListItem } from '@mui/material';

const Cloth = ({id, itemData, onSelectionChange}) => {
    const [selected, setSelected] = useState(null)

    const selectImg = (img) => {
        if (selected != img) {
            setSelected(img)
        } else{

        }
        onSelectionChange(id, img)
    }

    return (
        <>
            <ImageList cols={5}>
                {itemData.map((item) => (
                    <ImageListItem key={item.img}>
                        <img 
                            onClick={() => selectImg(item.img)}
                            src={`${item.img}`}
                        />
                    </ImageListItem>
                ))}
            </ImageList>
        </>
    )
}

export default Cloth