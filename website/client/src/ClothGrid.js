
const ClothGrid = () => {
  return (
    <div className="container">
      <div className="row gx-3 gy-3">
        {upload &&
          <div className={colClass}>
            <div
              className={`card text-center ${selected === "uploaded" ? "border-primary" : ""}`}
              style={{
                cursor: "pointer",
                padding: "12px",
                aspectRatio: '1 / 1', // makes it square
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
              onClick={() => setSelected('uploaded')}
            >
              <ImageUpload handleUpload={(img) => selectImage(img)} />
            </div>
          </div>
        }

        {itemData.map((item) => (
          <div className={colClass} key={item.img}>
            <div
              className={`card position-relative ${selected === item.img ? "border-primary" : ""}`}
              style={{
                cursor: "pointer",
                overflow: 'hidden',
                aspectRatio: '1 / 1', // square
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
              onClick={() => selectImage(item.img)}
            >
              <img
                src={item.img}
                className="card-img-top"
                style={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'contain',
                }}
                alt="cloth"
              />
              {username &&
                <button
                  onClick={(e) => handleSave(e, item.img)}
                  className="btn position-absolute"
                  style={{
                    top: "8px",
                    right: "8px",
                    width: '32px',
                    height: '32px',
                    backgroundColor: savedImages.includes(item.img) ? 'red' : 'rgba(0,0,0,0.3)',
                    borderRadius: "0%", // square
                    border: "none",
                    color: "white",
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                  onMouseEnter={e => e.currentTarget.style.backgroundColor = savedImages.includes(item.img) ? 'darkred' : 'rgba(0,0,0,0.6)'}
                  onMouseLeave={e => e.currentTarget.style.backgroundColor = savedImages.includes(item.img) ? 'red' : 'rgba(0,0,0,0.3)'}
                >
                  {savedImages.includes(item.img) ? <HeartFill size={16} /> : <Heart size={16} />}
                </button>
              }
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
