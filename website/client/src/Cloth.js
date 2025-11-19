import React, { useState, useRef } from "react";
import { ImageList, ImageListItem } from '@mui/material';

const Cloth = ({id, itemData, num_cols}) => {
    const [selected, setSelected] = useState(null)

    const selectImg = (img) => {
        if (selected != img) {
            setSelected(img)
        } else{

        }
    }

    return (
        <div
            style={{
                maxHeight: '100vh',
                overflowY: 'scroll',
            }}
        >
            <ImageList cols={num_cols}>
                {itemData.map((item) => (
                    <ImageListItem 
                        key={item.img}
                        style={{
                            aspectRatio: "1 / 1",
                            width: "100%",
                            overflow: "hidden",
                        }}
                    >
                        <img 
                            onClick={() => selectImg(item.img)}
                            src={`${item.img}`}
                            style={{
                                width: "100%",
                                height: "100%",
                                objectFit: "contain"
                            }}

                        />
                    </ImageListItem>
                ))}
            </ImageList>
        </div>
    )
}

export default Cloth